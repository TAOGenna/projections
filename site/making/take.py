"""Films the landing's issue: take.html played frame by frame on a stopped clock, then cut to a looping video with a
clear ground, so the landing plays it instead of building the 3D object live.

  uv run python site/making/take.py        writes site/landing/take.{webm,mov,webp} and prints where the video sits

The take: closed, it opens, three spreads turn, they turn back, it closes, and the loop starts again on the same frame.
WebM (VP9 with alpha) is for Chrome and Firefox; Safari plays the .mov (HEVC with alpha, through VideoToolbox).
"""
import functools
import http.server
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / "landing"
FPS, DSF = 30, 1.5            # frames a second; device pixels per page pixel at the landing's full size
VIEW = (1280, 1150)           # take.html's window; its stage sits at (640, 350)
SHIFT = (1105 - 640, 205 - 350)  # take.html's stage to the landing's: where the video goes on the 1600 x 1000 page

# (when, what), in ms: a turn takes 950 ms, the cover's own 1300 ms
STEPS, t = [], 1800
STEPS.append((t, "issue.next()")); t += 1300 + 1600
for _ in range(3): STEPS.append((t, "issue.next()")); t += 950 + 1500
for _ in range(3): STEPS.append((t, "issue.prev()")); t += 950 + 450
STEPS.append((t, "issue.prev()")); t += 1300
END = t


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    handler = functools.partial(Quiet, directory=SITE)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def film(frames: Path):
    srv = serve()
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": VIEW[0], "height": VIEW[1]}, device_scale_factor=DSF)
        page.clock.install(time=0)
        page.goto(f"http://127.0.0.1:{srv.server_port}/making/take.html")
        page.wait_for_function("window.ready === true")
        page.clock.pause_at(10_000)
        steps, shown, n = list(STEPS), 0, round(END * FPS / 1000)
        for f in range(n):
            now = round(f * 1000 / FPS)
            page.clock.run_for(now - shown); shown = now
            while steps and steps[0][0] <= now: page.evaluate(steps.pop(0)[1])
            page.screenshot(path=frames / f"f{f:04d}.png", omit_background=True)
        b.close()
    srv.shutdown()
    return n


def main():
    tmp = Path(tempfile.mkdtemp())
    n = film(tmp)
    # the smallest box every frame fits in, a little room around it, even sides for the encoders
    box = None
    for f in range(n):
        bb = Image.open(tmp / f"f{f:04d}.png").getchannel("A").getbbox()
        if bb: box = bb if box is None else (min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3]))
    W, H = round(VIEW[0] * DSF), round(VIEW[1] * DSF)
    l, t = max(0, box[0] - 6) // 2 * 2, max(0, box[1] - 6) // 2 * 2
    r, b = min(W, box[2] + 6), min(H, box[3] + 6)
    r, b = l + (r - l + 1) // 2 * 2, t + (b - t + 1) // 2 * 2
    crop = ["-vf", f"crop={r - l}:{b - t}:{l}:{t}"]
    src = ["-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%04d.png")]
    subprocess.run(["ffmpeg", *src, *crop, "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "36",
                    "-row-mt", "1", "-an", str(OUT / "take.webm")], check=True)
    subprocess.run(["ffmpeg", *src, *crop, "-c:v", "hevc_videotoolbox", "-alpha_quality", "0.8", "-q:v", "55",
                    "-tag:v", "hvc1", "-an", str(OUT / "take.mov")], check=True)
    Image.open(tmp / "f0000.png").crop((l, t, r, b)).save(OUT / "take.webp", quality=85)
    shutil.rmtree(tmp)
    x, y = SHIFT[0] + l / DSF, SHIFT[1] + t / DSF
    print(f"{n} frames, {END / 1000:.1f} s")
    print(f".take {{ left: {x:.1f}px; top: {y:.1f}px; width: {(r - l) / DSF:.1f}px; height: {(b - t) / DSF:.1f}px; }}")
    for f in ("take.webm", "take.mov", "take.webp"): print(f, f"{(OUT / f).stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
