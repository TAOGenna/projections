"""The issue as a PDF of single pages, printed by Chromium the way a browser prints it: reader.js cuts every spread
at the gutter into its two 8 × 10in pages, and the cover keeps its right half, the front of a closed magazine."""
import base64
import hashlib
import io
from pathlib import Path

JPEG_OVER = 100_000  # pixels: a lossless image larger than this is kept as a JPEG


def _shrink(pdf) -> None:
    """Chromium embeds an image again on every page that shows it, and keeps every WebP and PNG lossless.
    One copy of each, and JPEG for the big ones, takes an issue from hundreds of MB to tens."""
    import pikepdf
    seen = {}
    for o in list(pdf.objects):
        res = o.get("/Resources") if isinstance(o, (pikepdf.Dictionary, pikepdf.Stream)) else None
        xo = res.get("/XObject") if res is not None else None
        for name in list(xo.keys()) if xo is not None else []:
            img = xo[name]
            if img.get("/Subtype") == "/Image":
                mask = img.SMask.read_raw_bytes() if "/SMask" in img else b""
                xo[name] = seen.setdefault(hashlib.sha1(img.read_raw_bytes() + mask).digest(), img)
    for o in pdf.objects:
        if not (isinstance(o, pikepdf.Stream) and o.get("/Subtype") == "/Image" and o.get("/Filter") == "/FlateDecode"
                and o.get("/BitsPerComponent") == 8 and o.Width * o.Height > JPEG_OVER):
            continue
        im = pikepdf.PdfImage(o).as_pil_image()
        im = im if im.mode == "L" else im.convert("RGB")  # transparency stays in the image's own /SMask
        jpeg = io.BytesIO()
        im.save(jpeg, "JPEG", quality=85)
        if jpeg.tell() < len(o.read_raw_bytes()):
            o.write(jpeg.getvalue(), filter=pikepdf.Name.DCTDecode)
            o.ColorSpace = pikepdf.Name.DeviceGray if im.mode == "L" else pikepdf.Name.DeviceRGB
    pdf.remove_unreferenced_resources()


def print_pdf(issue_dir: Path, out: Path) -> Path:
    import pikepdf
    from playwright.sync_api import sync_playwright
    raw = out.with_suffix(".raw.pdf")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto((issue_dir / "index.html").resolve().as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready")
        # printing fires beforeprint, where reader.js lays out the pages. The PDF is read back in chunks: a whole
        # issue is too big for Playwright's page.pdf() to hand over in one piece.
        cdp = page.context.new_cdp_session(page)
        stream = cdp.send("Page.printToPDF", {"preferCSSPageSize": True, "printBackground": True,
                                              "transferMode": "ReturnAsStream"})["stream"]
        with raw.open("wb") as f:
            while True:
                chunk = cdp.send("IO.read", {"handle": stream, "size": 1 << 22})
                f.write(base64.b64decode(chunk["data"]) if chunk.get("base64Encoded") else chunk["data"].encode())
                if chunk["eof"]:
                    break
        browser.close()
    try:
        with pikepdf.open(raw) as pdf:
            _shrink(pdf)
            pdf.save(out, object_stream_mode=pikepdf.ObjectStreamMode.generate)
    finally:
        raw.unlink(missing_ok=True)
    return out
