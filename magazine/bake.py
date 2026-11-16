"""Baking: heavy decoration becomes an image once, so turning a page doesn't redraw it.

A decorative SVG layer (aria-hidden) that holds a filter (painted fields, noise) or hundreds of elements (a cloud
of dots) is rendered at 2x, in place, with the page's own styles, and replaced by that image in index.html.
Light SVGs stay vector. Run after assemble; assemble rebuilds index.html from the chapters, unbaked.
"""
import hashlib
from io import BytesIO
from pathlib import Path

import lxml.html

HEAVY = 300  # elements in one layer before it is cheaper as an image
SPREAD = '//*[contains(concat(" ", normalize-space(@class), " "), " spread ")]'
ISOLATE = """(n) => {
  const el = document.querySelector(`[data-bake="${n}"]`), s = el.closest('.spread');
  document.querySelectorAll('.spread').forEach(x => x.classList.toggle('__check', x === s));
  s.querySelectorAll('*').forEach(x => { x.style.visibility = (x === el || x.contains(el) || el.contains(x)) ? '' : 'hidden'; });
  s.style.background = 'transparent';
  const r = el.getBoundingClientRect();
  return {x: r.left, y: r.top, width: r.width, height: r.height, item: s.dataset.item || 'spread'};
}"""
RESTORE = """() => document.querySelectorAll('.spread, .spread *').forEach(x => { x.style.visibility = ''; x.style.background = ''; })"""
ONE_AT_A_TIME = (".deck{position:static!important;transform:none!important} .spread{display:none!important}"
                 " .spread.__check{display:block!important;box-shadow:none!important} html,body{margin:0!important;background:transparent!important}")


def _heavy(svg) -> bool:
    decorative = svg.get("aria-hidden") == "true" or bool(svg.xpath('ancestor::*[@aria-hidden="true"]'))
    return decorative and (bool(svg.xpath(".//*[local-name()='filter']")) or len(svg.xpath(".//*")) > HEAVY)


def bake(issue_dir: Path) -> int:
    """Bake every heavy decorative SVG layer in index.html into art/<item>-<n>.webp. Returns how many."""
    from PIL import Image
    from playwright.sync_api import sync_playwright
    index = issue_dir / "index.html"
    doc = lxml.html.document_fromstring(index.read_text())
    layers = [svg for svg in doc.xpath(SPREAD + "//svg") if _heavy(svg)]
    if not layers:
        return 0
    for n, svg in enumerate(layers):
        svg.set("data-bake", str(n))
    marked = issue_dir / ".bake.html"
    marked.write_text(lxml.html.tostring(doc, encoding="unicode", doctype="<!doctype html>"))
    (issue_dir / "art").mkdir(exist_ok=True)
    counts: dict[str, int] = {}
    seen: dict[str, str] = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=2)
            page.goto(marked.resolve().as_uri(), wait_until="load")
            page.add_style_tag(content=ONE_AT_A_TIME)
            page.evaluate("document.fonts.ready")
            for n, svg in enumerate(layers):
                box = page.evaluate(ISOLATE, n)
                shot = page.screenshot(omit_background=True, clip={k: box[k] for k in ("x", "y", "width", "height")})
                page.evaluate(RESTORE)
                im = Image.open(BytesIO(shot))
                if svg.xpath(".//*[local-name()='filter']"):  # a painted field is soft: 1x loses nothing
                    im = im.resize((round(box["width"]), round(box["height"])), Image.LANCZOS)
                key = hashlib.sha1(im.tobytes()).hexdigest()
                if key not in seen:  # the same field on several spreads: one file, decoded once
                    counts[box["item"]] = counts.get(box["item"], 0) + 1
                    seen[key] = f"{box['item']}-{counts[box['item']]}.webp"
                    im.save(issue_dir / "art" / seen[key], "WEBP", quality=90, method=6)
                name = seen[key]
                img = lxml.html.Element("img", {"src": f"art/{name}", "alt": "", "aria-hidden": "true", "decoding": "async",
                                                "class": svg.get("class", ""), "width": f"{box['width']:.0f}",
                                                "height": f"{box['height']:.0f}"})
                if svg.get("style"):
                    img.set("style", svg.get("style"))
                img.tail = svg.tail
                svg.getparent().replace(svg, img)
            browser.close()
    finally:
        marked.unlink(missing_ok=True)
    index.write_text(lxml.html.tostring(doc, encoding="unicode", doctype="<!doctype html>"))
    return len(layers)
