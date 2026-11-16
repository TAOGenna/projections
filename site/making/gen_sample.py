"""Writes the site's sample issue (site/sample) from three pieces of the owner's reading list, then fits it.

  uv run python site/making/gen_sample.py        write chapters from ranges.json (or a first guess)
  uv run python site/making/gen_sample.py fit    fit every item's blocks into its spreads in the real page

The openers' drawings are ours, computed from each piece's own material; every piece is credited in the colophon.
"""
import json
import math
import random
import shutil
import sys
from html import escape
from pathlib import Path

import lxml.html

ROOT = Path(__file__).resolve().parents[2]
ISSUE = ROOT / "site" / "sample"
CH = ISSUE / "chapters"
RANGES = Path(__file__).resolve().parent / "ranges.json"
RUN = "Projections · Nº 00"
JP, MU, MM = "sophielwang-blog-jpeg", "jeremybernste-writing-deriving-muon", "seb-v-github-01-20-fast-gpu-matrix-multiplicatio"
ITEMS = [JP, MU, MM]
CREDIT = "The front is a drawing by Taili Zhuang, from his 2020 portfolio"


# ---------------------------------------------------------------- the pieces' own words
def blocks(slug):
    src = (ISSUE / "items" / slug / "source.html").read_text()
    return [e for e in lxml.html.fragments_fromstring(src) if not isinstance(e, str)]






# ---------------------------------------------------------------- the house: type, tones, grounds
HOUSE_TYPE = """
[data-item] .W { color: var(--body); font-family: var(--house) !important; font-weight: 300; font-size: 13.5px; line-height: 1.6;
  text-align: justify; hyphens: auto; }
[data-item] .W :is(p, li, td, th, dd, dt, blockquote, figcaption, span, a, em, i, b, strong) { font-family: var(--house) !important; }
[data-item] .W :is(b, strong, th) { font-weight: 600; }
[data-item] .W :is(h1, h2, h3, h4, h5, h6) { color: var(--ink); font-family: var(--display) !important; font-weight: 500 !important;
  text-transform: uppercase; letter-spacing: .08em; line-height: 1.2 !important; text-align: left; hyphens: manual; }
[data-item] .W h1 { font-size: 21px !important; } [data-item] .W h2 { font-size: 17px !important; }
[data-item] .W :is(h3, h4, h5, h6) { font-size: 15px !important; }
[data-item] .W :is(pre, code, kbd, samp, pre *) { font-family: Menlo, ui-monospace, monospace !important; font-weight: 400; }
[data-item] .W table { font-size: 12.5px; text-align: left; }
[data-item] .W img { max-width: 100%; height: auto; }
"""
WORLDS = {  # each piece's own colours and structure, in the house's type
    JP: ("#fff", """.W p { margin: 0 0 9px; } .W ul { padding-left: 18px; }
.W img { display: block; max-height: 330px; width: auto; margin: 4px auto 10px; }"""),
    MU: ("#c3fcb3", """.W p { margin: 0 0 9px; } .W a { color: #06099c; }
.W img { display: block; margin: 6px auto 10px; border: 2.5px solid #000; } .W math[display="block"] { margin: 4px 0 10px; }"""),
    MM: ("#fdfdfd", """.W p { margin: 0 0 8px; } .W a { color: #2a7ae2; text-decoration: none; }
.W pre { background: #eeeeff; padding: 8px 10px; white-space: pre-wrap; font-size: 10.5px; line-height: 1.45; margin: 0 0 10px; }
.W code { font-size: 11px; } .W img { display: block; margin: 4px auto 6px; }
.W table { border-collapse: collapse; width: 100%; font-size: 11px; } .W th, .W td { border-bottom: 1px solid #ddd; padding: 2px 4px; }"""),
}


def world(slug):
    paper, css = WORLDS[slug]
    scoped = css.replace(".W", f'[data-item="{slug}"] .W')
    return f'<style>\n[data-item="{slug}"] {{ --paper: {paper}; }}\n{scoped}\n</style>\n'




def svg(body):
    return f'<svg class="layer" aria-hidden="true" width="1600" height="1000">{body}</svg>'


MONO = "Menlo, ui-monospace, monospace"




def field(name, dark, seed):
    return svg(f'<filter id="f-{name}"><feTurbulence type="fractalNoise" baseFrequency=".0035 .006" numOctaves="4" seed="{seed}"/>'
               '<feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2.2 0 0 0 -.75" result="m"/>'
               f'<feComposite in="SourceGraphic" in2="m" operator="in"/></filter><rect width="1600" height="1000" fill="{dark}" '
               f'filter="url(#f-{name})"/>')


GRAIN = '<div class="grain" aria-hidden="true"></div>'


def construct(circles=(), cols=15):
    lines = "".join(f'<line x1="{60 + k * 1480 / (cols - 1):.0f}" y1="0" x2="{60 + k * 1480 / (cols - 1):.0f}" y2="1000" '
                    f'stroke="var(--hair)" stroke-width=".6" opacity=".2"/>' for k in range(cols))
    rings = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="var(--hair)" stroke-width=".7" opacity=".38"/>'
                    for x, y, r in circles)
    return svg(lines + rings)


def obj(slug, src, left, top, width, num="", blend="multiply"):
    """One of the piece's own pictures standing on the ground at scale, like the sculptures on Taili's shelf."""
    n = f'<span class="obj-num" style="left:{left}px;top:{top - 18}px">{num}.</span>' if num else ""
    return (f'<img class="obj" src="items/{slug}/{src}" alt="" style="left:{left}px;top:{top}px;width:{width}px;'
            f'mix-blend-mode:{blend}">{n}')


def framed(slug, src, left, top, width, cap, small):
    return (f'<figure class="framed" style="left:{left}px;top:{top}px;width:{width}px"><img src="items/{slug}/{src}" alt="">'
            f'<figcaption class="cap">{escape(cap)}<small>{escape(small)}</small></figcaption></figure>')




def caption(left, top, width, line, small):
    return (f'<div class="cap" style="position:absolute;left:{left}px;top:{top}px;width:{width}px">{escape(line)}'
            f'<small>{escape(small)}</small></div>')




# ---------------------------------------------------------------- the openers: invitations, not explanations
# Words live in the box. Outside it: the piece's own pictures and objects drawn from it, at scale, each with at most
# a two-line label naming it (policies.md, "The opener is an invitation").
DRAWN = ISSUE / "drawn"


def label_at(left, top, width, line, small):
    return caption(left, top, width, line, small)


# ---------------------------------------------------------------- I · JPEG: the flamingos, five times, at falling quality
def jpeg_plates(qualities=(85, 15, 7, 3, 1)):
    """The essay's photograph, one flamingo crop, saved as JPEG again and again at lower quality: the real algorithm."""
    from PIL import Image
    DRAWN.mkdir(exist_ok=True)
    crop = Image.open(ISSUE / "items" / JP / "img" / "01.webp").convert("RGB").crop((300, 440, 600, 840))
    for q in qualities:
        crop.save(DRAWN / f"jpeg-q{q:02}.jpg", "JPEG", quality=q)
    return [f"drawn/jpeg-q{q:02}.jpg" for q in qualities]


def cosines(left, top, size=48, gap=8):
    """JPEG's sixty-four cosine patterns, as a field of tiles."""
    out, s = [], size / 8
    for v in range(8):
        for u in range(8):
            x0, y0 = left + u * (size + gap), top + v * (size + gap)
            for y in range(8):
                for x in range(8):
                    g = round(128 + 120 * math.cos((2 * x + 1) * u * math.pi / 16) * math.cos((2 * y + 1) * v * math.pi / 16))
                    out.append(f'<rect x="{x0 + x * s:.1f}" y="{y0 + y * s:.1f}" width="{s + .3:.1f}" height="{s + .3:.1f}" '
                               f'fill="rgb({g},{g},{g - 6})"/>')
    return svg("".join(out))


def jpeg_comp():
    plates = "".join(f'<img class="obj plate" src="{src}" alt="" style="left:{60 + k * 250}px;top:648px;width:218px">'
                     for k, src in enumerate(jpeg_plates()))
    return {"tone": ("light", "#f3f0ea"),
            "html": field("jp", "#e8e2d6", 4) + GRAIN + construct([(1316, 294, 300)])
            + cosines(1092, 70) + plates
            + label_at(1092, 530, 448, "The sixty-four cosines", "drawn for this issue")
            + label_at(1320, 890, 220, "The flamingos, five times", "JPEG at falling quality, from the essay's photograph")}


# ---------------------------------------------------------------- II · Muon: singular values, iterated, as tracks
NAVY = "#06099c"


def smooth(points):
    """A curve through the points that leaves and enters each row straight down: no overshoot, like a flow."""
    d = f"M{points[0][0]:.1f},{points[0][1]:.1f}"
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        m = (y2 - y1) / 2
        d += f"C{x1:.1f},{y1 + m:.1f} {x2:.1f},{y2 - m:.1f} {x2:.1f},{y2:.1f}"
    return d


def tracks():
    """Singular values under the post's cubic p(x) = 3/2 x - 1/2 x^3, iterated: every track ends at one."""
    p = lambda x: 1.5 * x - .5 * x ** 3
    sx = lambda v: 30 + 1540 * v / 1.74
    out, rows, top, step = [], 10, 652, 32
    for k in range(48):
        v = .02 + 1.7 * (k + .5) / 48
        pts = [(sx(v), top)]
        for r in range(1, rows):
            v = p(v)
            pts.append((sx(v), top + r * step))
        out.append(f'<path d="{smooth(pts)}" fill="none" stroke="{NAVY}" stroke-width=".9" opacity="{.25 + .5 * (k % 3 == 0)}"/>')
        out.append(f'<circle cx="{pts[0][0]:.1f}" cy="{top}" r="2.4" fill="{NAVY}" opacity=".7"/>')
    out.append(f'<line x1="{sx(1):.1f}" y1="{top + (rows - 1) * step}" x2="{sx(1):.1f}" y2="1000" stroke="{NAVY}" stroke-width="1.6"/>')
    return svg("".join(out))


def muon_comp():
    return {"tone": ("light", "#c3fcb3"),
            "html": field("mu", "#b0ec9f", 6) + GRAIN + construct([(1180, 300, 330)])
            + '<div class="bleed" aria-hidden="true">' + tracks() + "</div>"
            + framed(MU, "img/01.jpg", 880, 70, 520, "Particle tracks in a bubble chamber", "the post's own photograph, Fermilab")
            + label_at(1330, 560, 210, "Singular values, iterated", "drawn for this issue, with the post's cubic")}


# ---------------------------------------------------------------- III · matrix multiplication: the product as an object
# The post's own numbers: 4096 x 4096 matrices; a workgroup of 256 threads computes a 128 x 128 tile of C; K is fed
# 8 at a time (BK); each thread computes an 8 x 8 tile of outputs. Drawn in the colours and the hand of its sketches.
PINK, YELLOW, GREEN, INK_MM = "#f2a7b8", "#f5dc6e", "#9fd68c", "#2b2b30"
TILE = (20, 11)  # the tile of C lifted: row band 20, column band 11 of 32
mm_rnd = random.Random(5)


def hand(pts, w=1.1, o=.9, close=False, color=INK_MM):
    """A line drawn by hand, as in the post's sketches: a little unsteady, gone over once."""
    out = []
    for k, (jit, ww, oo) in enumerate(((.7, w, o), (1.2, w * .45, o * .5))):
        p = [(x + mm_rnd.uniform(-jit, jit), y + mm_rnd.uniform(-jit, jit)) for x, y in pts]
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in p) + (" Z" if close else "")
        out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{ww:.2f}" opacity="{oo:.2f}" '
                   'stroke-linecap="round" stroke-linejoin="round"/>')
    return "".join(out)


def face(pts, fill, alpha):
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    return f'<path d="{d}" fill="{fill}" fill-opacity="{alpha}" stroke="none"/>'


def matmul_cube(ox=1172, oy=468, s=322):
    """C on the floor, A on the left wall, B on the back wall; one tile of C rises through the depth, its strip of A
    and its strip of B lit, the K slices across it."""
    c, sn = math.cos(math.pi / 6), math.sin(math.pi / 6)
    P = lambda x, y, z: (ox + (x - y) * c * s, oy + (x + y) * sn * s - z * s)
    i, j = TILE
    y0, y1, x0, x1 = i / 32, (i + 1) / 32, j / 32, (j + 1) / 32
    out = []
    # the three matrices, faintly tinted
    out.append(face([P(0, 0, 0), P(1, 0, 0), P(1, 1, 0), P(0, 1, 0)], PINK, .2))      # C
    out.append(face([P(0, 0, 0), P(0, 1, 0), P(0, 1, 1), P(0, 0, 1)], YELLOW, .2))    # A
    out.append(face([P(0, 0, 0), P(1, 0, 0), P(1, 0, 1), P(0, 0, 1)], GREEN, .2))     # B
    for k in range(1, 32):  # their 128-wide bands
        t = k / 32
        out.append(hand([P(t, 0, 0), P(t, 1, 0)], .35, .35) + hand([P(0, t, 0), P(1, t, 0)], .35, .35))
        out.append(hand([P(0, t, 0), P(0, t, 1)], .35, .3) + hand([P(t, 0, 0), P(t, 0, 1)], .35, .3))
    # the lit strips of A and B, and the tile of C
    out.append(face([P(0, y0, 0), P(0, y1, 0), P(0, y1, 1), P(0, y0, 1)], YELLOW, .85))
    out.append(face([P(x0, 0, 0), P(x1, 0, 0), P(x1, 0, 1), P(x0, 0, 1)], GREEN, .85))
    out.append(face([P(x0, y0, 0), P(x1, y0, 0), P(x1, y1, 0), P(x0, y1, 0)], PINK, .95))
    for z in [k / 16 for k in range(1, 16)]:  # slices of K as they are fed, BK at a time
        out.append(hand([P(0, y0, z), P(0, y1, z)], .5, .5) + hand([P(x0, 0, z), P(x1, 0, z)], .5, .5))
    # the column of work above the tile: a translucent prism, sliced the same way
    out.append(face([P(x1, y0, 0), P(x1, y1, 0), P(x1, y1, 1), P(x1, y0, 1)], PINK, .22))
    out.append(face([P(x0, y1, 0), P(x1, y1, 0), P(x1, y1, 1), P(x0, y1, 1)], PINK, .3))
    out.append(face([P(x0, y0, 1), P(x1, y0, 1), P(x1, y1, 1), P(x0, y1, 1)], PINK, .55))
    for z in [k / 16 for k in range(1, 16)]:
        out.append(hand([P(x1, y0, z), P(x1, y1, z), P(x0, y1, z)], .45, .45))
    for a, b in (((x1, y0), (x1, y0)), ((x1, y1), (x1, y1)), ((x0, y1), (x0, y1))):
        out.append(hand([P(*a, 0), P(*b, 1)], .8, .8))
    out.append(hand([P(x0, y0, 1), P(x1, y0, 1), P(x1, y1, 1), P(x0, y1, 1)], .8, .8, close=True))
    # dashed lines carrying A across to the prism, and B forward to it
    for z in (.25, .5, .75):
        for y in (y0, y1):
            (ax, ay), (bx, by) = P(0, y, z), P(x0, y, z)
            out.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{INK_MM}" stroke-width=".6" '
                       'stroke-dasharray="3 4" opacity=".45"/>')
        for x in (x0, x1):
            (ax, ay), (bx, by) = P(x, 0, z), P(x, y0, z)
            out.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{INK_MM}" stroke-width=".6" '
                       'stroke-dasharray="3 4" opacity=".45"/>')
    # the outlines of the three matrices, by hand
    out.append(hand([P(0, 0, 0), P(1, 0, 0), P(1, 1, 0), P(0, 1, 0)], 1.6, 1, close=True))
    out.append(hand([P(0, 1, 0), P(0, 1, 1), P(0, 0, 1), P(1, 0, 1), P(1, 0, 0)], 1.6, 1))
    out.append(hand([P(0, 0, 0), P(0, 0, 1)], 1.2, .85))
    out.append(hand([P(x0, y0, 0), P(x1, y0, 0), P(x1, y1, 0), P(x0, y1, 0)], 1.1, .95, close=True))
    return svg("".join(out))


def zoom_series(left=64, top=700, size=118, gap=56):
    """One output of C at four scales: C's 32 x 32 tiles; a tile's 16 x 16 threads; a thread's 8 x 8 outputs; one
    output, a row of A met by a column of B."""
    out, boxes = [], []
    picks = [(TILE, 32, PINK), ((5, 9), 16, YELLOW), ((3, 6), 8, GREEN)]
    for n, ((r, cidx), cells, color) in enumerate(picks):
        x, y = left + n * (size + gap), top
        q = size / cells
        out.append(face([(x, y), (x + size, y), (x + size, y + size), (x, y + size)], "#fff", .7))
        for k in range(1, cells):
            out.append(hand([(x + k * q, y), (x + k * q, y + size)], .3, .35, color="#555"))
            out.append(hand([(x, y + k * q), (x + size, y + k * q)], .3, .35, color="#555"))
        cx, cy = x + cidx * q, y + r * q
        out.append(face([(cx, cy), (cx + q, cy), (cx + q, cy + q), (cx, cy + q)], color, .95))
        out.append(hand([(cx, cy), (cx + q, cy), (cx + q, cy + q), (cx, cy + q)], .8, .9, close=True))
        out.append(hand([(x, y), (x + size, y), (x + size, y + size), (x, y + size)], 1.1, .95, close=True))
        boxes.append((cx, cy, q))
    x, y = left + 3 * (size + gap), top  # one output: a row of A and a column of B crossing
    out.append(face([(x, y), (x + size, y), (x + size, y + size), (x, y + size)], "#fff", .7))
    out.append(face([(x, y + size * .42), (x + size, y + size * .42), (x + size, y + size * .58), (x, y + size * .58)], YELLOW, .9))
    out.append(face([(x + size * .42, y), (x + size * .58, y), (x + size * .58, y + size), (x + size * .42, y + size)], GREEN, .85))
    out.append(face([(x + size * .42, y + size * .42), (x + size * .58, y + size * .42), (x + size * .58, y + size * .58),
                     (x + size * .42, y + size * .58)], PINK, 1))
    out.append(hand([(x, y), (x + size, y), (x + size, y + size), (x, y + size)], 1.1, .95, close=True))
    for n, (cx, cy, q) in enumerate(boxes):  # each picked cell opens into the next square
        nx = left + (n + 1) * (size + gap)
        for (ax, ay), (bx, by) in (((cx + q, cy), (nx, top)), ((cx + q, cy + q), (nx, top + size))):
            out.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{INK_MM}" stroke-width=".6" '
                       'stroke-dasharray="3 4" opacity=".5"/>')
    return svg("".join(out))


def matmul_comp():
    return {"tone": ("light", "#eeeef3"),
            "html": field("mm", "#e2e2ec", 5) + GRAIN + construct([(1190, 478, 380)])
            + matmul_cube() + zoom_series()
            + obj(MM, "img/04.jpg", 1336, 78, 204)
            + label_at(1336, 238, 204, "A SIMD", "the post's own drawing")
            + obj(MM, "img/31.jpg", 836, 792, 140) + obj(MM, "img/32.jpg", 992, 792, 140)
            + label_at(836, 912, 300, "LDS banks, before and after", "the post's own drawings")
            + label_at(64, 838, 660, "One output of C, at four scales",
                       "a tile of 128 × 128, a thread's 8 × 8, one row of A meeting one column of B")
            + label_at(1250, 872, 290, "A × B = C, as a cube",
                       "4096 × 4096; one tile rising through it, fed 8 at a time; drawn for this issue")}


# ---------------------------------------------------------------- spreads
class Issue:
    def __init__(self):
        self.k, self.starts = 2, {}

    def spread(self, slug, body, runr, opener=False, cls="gutter", tone_=None, decor=""):
        self.k += 1
        left, right = 2 * (self.k - 1), 2 * (self.k - 1) + 1
        self.starts.setdefault(slug, left)
        sec = f' data-tone="{tone_[0]}" style="--paper:{tone_[1]}"' if tone_ else ""
        heads = ("" if opener else f'<div class="runhead l">{RUN}</div>') + f'<div class="runhead r">{runr}</div>'
        return (f'<section class="spread {cls}" data-item="{slug}"{sec}>\n{decor}{heads}\n{body}\n'
                f'<div class="folio l">{left}</div><div class="folio r">{right}</div>\n</section>\n')

    def chapter(self, slug, numeral, title, sub, meta_, note, comp, ranges):
        left = (f'<div class="page l"><div class="box"><div class="numeral"><span>{numeral}</span></div>'
                f'<div class="ch-title">{title}</div><div class="ch-sub">{sub}</div><div class="ch-meta">{meta_}</div>'
                f'<div class="box-note editor">{note}</div></div></div>')
        out = self.spread(slug, left, title, opener=True, tone_=comp.get("tone"), decor=comp.get("html", ""))
        for _, a, b in ranges:
            xs = f'<x-src item="{slug}" b="{a}"></x-src>' if a == b else f'<x-src item="{slug}" from="{a}" to="{b}"></x-src>'
            out += self.spread(slug, f'<div class="flow wide W">{xs}</div>', title)
        return out


def write_chapters():
    R = json.loads(RANGES.read_text()) if RANGES.exists() else {s: [["wide", 1, len(blocks(s))]] for s in ITEMS}
    iss, ch = Issue(), {}
    ch["02-jpeg.html"] = world(JP) + iss.chapter(
        JP, "I", "JPEG Compression", "how a photograph loses what you wouldn't miss",
        'Sophie Wang · 13 March 2026<br><a href="https://www.sophielwang.com/blog/jpeg">sophielwang.com/blog/jpeg</a>',
        "<p>A short essay on how JPEG decides what a photograph can lose without your noticing, told through one "
        "picture of flamingos, with every formula in its place.</p>",
        jpeg_comp(), R[JP])
    ch["03-muon.html"] = world(MU) + iss.chapter(
        MU, "II", "Deriving Muon", "an optimizer derived from a single principle",
        'Jeremy Bernstein · Boston, 7 March 2025<br>'
        '<a href="https://jeremybernste.in/writing/deriving-muon">jeremybernste.in/writing/deriving-muon</a>',
        "<p>The Muon optimizer, derived from one exact principle in four steps, on the author's own green page.</p>",
        muon_comp(), R[MU])
    ch["04-matmul.html"] = world(MM) + iss.chapter(
        MM, "III", "Matrix Multiplication on RDNA3", "50 TFLOPS, and 60% faster than rocBLAS",
        'Seb-V · 12 January 2025<br><a href="https://seb-v.github.io/optimization/update/2025/01/20/'
        'Fast-GPU-Matrix-multiplication.html">seb-v.github.io</a>',
        "<p>One matrix multiplication on an AMD Radeon 7900 XTX, written eight times, each kernel faster than the last, "
        "with every listing, profile and hand-drawn diagram along the way.</p>",
        matmul_comp(), R[MM])
    credits = "".join(f"<p><i>{escape(t)}</i>, {escape(a)}. {escape(u)}</p>" for t, a, u in (
        ("JPEG compression", "Sophie Wang, 13 March 2026", "sophielwang.com/blog/jpeg"),
        ("Deriving Muon", "Jeremy Bernstein, 7 March 2025", "jeremybernste.in/writing/deriving-muon"),
        ("Optimizing Matrix Multiplication on RDNA3: 50 TFlops and 60% Faster Than rocBLAS", "Seb-V, 12 January 2025",
         "seb-v.github.io")))
    colophon = ('<div class="colophon editor"><h2>COLOPHON</h2><p>Projections Nº 00, a sample issue: three pieces from one '
                f"reading list, each in full and in its own world, set by the real pipeline.</p>{credits}"
                f"<p>The words and pictures are their authors'. {CREDIT}. The drawings on the openers are ours.</p></div>")
    ch["99-back.html"] = """<style>
[data-item="_back"] .colophon { position: absolute; left: 400px; top: 250px; width: 800px; text-align: center; }
[data-item="_back"] .colophon h2 { font: 400 26px/1 var(--display); letter-spacing: .14em; color: var(--ink); margin: 0 0 28px; }
[data-item="_back"] .colophon p { text-indent: 0; text-align: center; margin: 0 0 10px; }
</style>
""" + iss.spread("_back", construct([(800, 500, 360), (800, 500, 200)]) + colophon, "Colophon", opener=True,
                 tone_=("light", "#fcf3ec"), cls="")
    ch["00-cover.html"] = ('<section class="spread" id="front" data-item="_cover">\n<img class="art" src="../cover.jpg" alt="">\n'
                           '<div class="brand">Projections</div>\n<div class="issue">Nº 00 · A SAMPLE ISSUE</div>\n</section>\n')
    toc = [("I", "JPEG Compression", "sophielwang.com · an essay", JP), ("II", "Deriving Muon", "jeremybernste.in · a derivation", MU),
           ("III", "Matrix Multiplication on RDNA3", "seb-v.github.io · a post", MM)]
    rows = "".join(f'<div class="toc-row" style="top:{300 + 170 * i}px"></div><div class="toc-num" style="top:{300 + 170 * i - 57}px">{n}</div>'
                   f'<div class="toc-t" style="top:{300 + 170 * i - 32}px">{t}<small>{s} · p. {iss.starts[slug]}</small></div>'
                   for i, (n, t, s, slug) in enumerate(toc))
    ch["01-contents.html"] = (f'<section class="spread" id="contents" data-item="_contents">\n<div class="toc-box">'
                              f'<div class="toc-head">CONTENTS</div></div>\n{rows}\n<div class="folio l">2</div><div class="folio r">3</div>\n</section>\n')
    if CH.exists():
        shutil.rmtree(CH)
    CH.mkdir(parents=True)
    for name, html in ch.items():
        (CH / name).write_text(html)
    style = (ROOT / "issues" / "2026-11" / "style.css").read_text() + "\n/* the sample */\n" + HOUSE_TYPE + """
.plate { box-shadow: 0 14px 26px -12px rgba(60, 40, 20, .45); }
"""
    (ISSUE / "style.css").write_text(style)
    print(f"wrote {len(ch)} chapters, {iss.k} spreads; starts {iss.starts}")


# ---------------------------------------------------------------- fitting
FIT_JS = """([slug, blocks]) => {
  let host = document.querySelector('.spread.__fit');
  if (!host) { host = document.createElement('section'); document.querySelector('.deck').appendChild(host); }
  host.className = 'spread __fit __check'; host.dataset.item = slug; host.innerHTML = '';
  document.querySelectorAll('.spread').forEach(s => { if (s !== host) s.classList.remove('__check'); });
  const box = document.createElement('div'); box.className = 'flow wide W'; host.appendChild(box);
  const over = () => box.scrollWidth > box.clientWidth + 1 || box.scrollHeight > box.clientHeight + 1;
  let n = 0;
  for (const html of blocks) {
    const t = document.createElement('template'); t.innerHTML = html; box.appendChild(t.content.firstElementChild);
    if (over()) { if (n > 0) box.lastElementChild.remove(); else n = 1; break; }
    n++;
  }
  return n;
}"""
WAIT_IMAGES = ("async () => { await Promise.all([...document.images].map(i => { i.loading = 'eager'; "
               "return i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; }); })); }")


def fit():
    from playwright.sync_api import sync_playwright
    sys.path.insert(0, str(ROOT))
    from magazine.assemble import expand_sources
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1600, "height": 1000})
        pg.goto((ISSUE / "index.html").resolve().as_uri(), wait_until="load")
        pg.add_style_tag(content=".deck{position:static!important;transform:none!important} .spread{display:none!important} "
                                 ".spread.__check{display:block!important}")
        pg.evaluate("""Promise.all(['300 14px "Open Sans"', '600 14px "Open Sans"', 'italic 300 14px "Open Sans"',
                       '500 20px "Cormorant Garamond"'].map(f => document.fonts.load(f)))""")
        for slug in ITEMS:
            total, n, ranges = len(blocks(slug)), 1, []
            while n <= total:
                html = [expand_sources(f'<x-src item="{slug}" b="{i}"></x-src>', ISSUE / "items") for i in range(n, total + 1)]
                pg.evaluate(FIT_JS, [slug, html])
                pg.evaluate(WAIT_IMAGES)
                got = pg.evaluate(FIT_JS, [slug, html])
                ranges.append(["wide", n, n + got - 1])
                n += got
            out[slug] = ranges
            print(slug, ranges)
        b.close()
    RANGES.write_text(json.dumps(out, indent=1))


def pages(scale=1.25):
    """Every spread of the built sample as two page images, for the landing's printed issue: site/landing/pages."""
    from PIL import Image
    from playwright.sync_api import sync_playwright
    out = ROOT / "site" / "landing" / "pages"
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=scale)
        pg.goto((ISSUE / "index.html").resolve().as_uri(), wait_until="networkidle")
        pg.add_style_tag(content=".deck{position:static!important;transform:none!important} .spread{display:none!important} "
                                 ".spread.__shot{display:block!important}")
        pg.evaluate("document.fonts.ready")
        count = pg.evaluate("document.querySelectorAll('.spread').length")
        for n in range(1, count + 1):
            pg.evaluate(f"document.querySelectorAll('.spread').forEach((s, i) => s.classList.toggle('__shot', i === {n - 1}))")
            pg.evaluate(WAIT_IMAGES)
            shot = out / "_spread.png"
            pg.locator(".spread.__shot").screenshot(path=str(shot))
            im = Image.open(shot).convert("RGB")
            w, h = im.size
            im.crop((0, 0, w // 2, h)).save(out / f"s{n:02}-l.jpg", quality=82, optimize=True, progressive=True)
            im.crop((w // 2, 0, w, h)).save(out / f"s{n:02}-r.jpg", quality=82, optimize=True, progressive=True)
        shot.unlink()
        b.close()
    print(f"wrote {count} spreads to {out}")


if __name__ == "__main__":
    {"fit": fit, "pages": pages}.get(sys.argv[1] if sys.argv[1:] else "", write_chapters)()
