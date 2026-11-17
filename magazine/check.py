"""Checking an issue: every source block placed exactly once, nothing cut off, every image loaded."""
import json
from collections import Counter
from pathlib import Path

import lxml.html

# Shows one spread at a time, untransformed, at the top-left of a 1600 × 1000 viewport.
ONE_AT_A_TIME = """
html, body { margin: 0 !important; overflow: visible !important; }
.deck { position: static !important; transform: none !important; }
.spread { display: none !important; }
.spread.__check { display: block !important; box-shadow: none !important; }
"""

# How far (px) anything that would be lost sticks out of spread i, and which placed blocks can't be seen:
# - the spread's own scroll overflow (content beyond 1600 × 1000);
# - any element not inside a clipping box that sticks out past the spread (things meant to bleed go in an
#   overflow:hidden box);
# - any text that sticks out of the clipping or multi-column box it sits in (text spilled from columns is lost),
#   or that its own clipping box cuts off (overflow:auto, line clamps);
# - source blocks that render nothing (display:none, visibility:hidden);
# - content the PDF would cut: a line of text or a figure across the gutter at 800px, or text within the 60px either
#   side of it (each page printed alone keeps a margin there). Decoration (aria-hidden) and the cover may cross.
MEASURE_JS = """async (i) => {
  await document.fonts.ready;
  const s = document.querySelectorAll('.spread')[i], sr = s.getBoundingClientRect();
  const out = (r, b) => Math.max(r.right - b.right, r.bottom - b.bottom, b.left - r.left, b.top - r.top, 0);
  const clipping = cs => cs.overflowX !== 'visible' || cs.overflowY !== 'visible';
  let over = Math.max(s.scrollHeight - s.clientHeight, s.scrollWidth - s.clientWidth, 0);
  const hidden = [], faked = new Set();
  const faces = fam => [...document.fonts].filter(f => f.family.replace(/["']/g, '') === fam);
  const heaviest = fs => Math.max(...fs.map(f => Math.max(...String(f.weight).split(' ').map(Number))));
  for (const el of s.querySelectorAll('[data-src][data-b]')) {
    if (!el.getClientRects().length || getComputedStyle(el).visibility === 'hidden') hidden.push(el.dataset.b);
  }
  for (const el of s.querySelectorAll('*')) {
    if (el.closest('[aria-hidden="true"]')) continue;  // decoration: bleeds on purpose, isn't content
    const rects = [...el.getClientRects()].filter(r => r.width > 0 && r.height > 0);
    if (!rects.length) continue;
    let clipped = false;
    for (let a = el.parentElement; a && a !== s; a = a.parentElement) if (clipping(getComputedStyle(a))) { clipped = true; break; }
    if (!clipped) for (const r of rects) over = Math.max(over, out(r, sr));
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    const cs0 = getComputedStyle(el), fam = cs0.fontFamily.split(',')[0].trim().replace(/["']/g, '');
    const fs = faces(fam), italic = cs0.fontStyle !== 'normal', weight = parseInt(cs0.fontWeight, 10);
    if (fs.length) {
      const same = fs.filter(f => (f.style !== 'normal') === italic);
      if (!same.length || (weight >= 600 && heaviest(same) < 600)) faked.add(`${fam} ${weight} ${italic ? 'italic' : 'normal'}`);
    }
    if (clipping(getComputedStyle(el))) over = Math.max(over, el.scrollHeight - el.clientHeight, el.scrollWidth - el.clientWidth);
    for (let a = el.parentElement; a && a !== s; a = a.parentElement) {
      const cs = getComputedStyle(a);
      if (clipping(cs) || cs.columnCount !== 'auto' || cs.columnWidth !== 'auto') {
        const br = a.getBoundingClientRect();
        for (const r of rects) over = Math.max(over, out(r, br));
      }
    }
  }
  const G = sr.left + 800, M = 60, cross = [], near = new Set();
  const seen = r => { const c = {l: r.left, r: r.right};  // the part of a box its clipping ancestors leave visible
    return el => { for (let a = el.parentElement; a && a !== s; a = a.parentElement) if (clipping(getComputedStyle(a))) {
      const b = a.getBoundingClientRect(); c.l = Math.max(c.l, b.left); c.r = Math.min(c.r, b.right); } return c; }; };
  if (s.dataset.item !== '_cover') {
    const walk = document.createTreeWalker(s, NodeFilter.SHOW_TEXT);
    for (let n; n = walk.nextNode();) {
      const el = n.parentElement;
      if (!n.textContent.trim() || el.closest('[aria-hidden="true"]')) continue;
      const range = document.createRange();
      range.selectNodeContents(n);
      for (const r of range.getClientRects()) {
        const c = seen(r)(el);
        if (c.r - c.l < 1) continue;
        if (c.l < G - 2 && c.r > G + 2) cross.push((el.closest('[data-b]') || el).dataset.b || el.tagName.toLowerCase());
        else if (c.l < G + M - 6 && c.r > G - M + 6) near.add(  // a glyph's few px of overhang is no layout
          (el.closest('[data-b]') || el).dataset.b || el.tagName.toLowerCase());
      }
    }
    for (const el of s.querySelectorAll('img, svg, video, canvas, iframe, table, pre, figure')) {
      if (el.closest('[aria-hidden="true"]') || el.parentElement.closest('svg, figure, table, pre')) continue;
      // each fragment on its own: a table that runs on from one page's column to the next is two pieces
      if ([...el.getClientRects()].map(r => seen(r)(el)).some(c => c.l < G - 2 && c.r > G + 2)) cross.push(el.tagName.toLowerCase() + (el.getAttribute('src') ? ' ' + el.getAttribute('src') : ''));
    }
  }
  return {over: Math.round(over), hidden, faked: [...faked], cross: [...new Set(cross)], near: [...near]};
}"""

IMAGES_JS = """async () => {
  await Promise.all([...document.images].map(img => {
    img.loading = 'eager';
    return img.complete ? 0 : new Promise(r => { img.onload = img.onerror = r; });
  }));
  return [...document.querySelectorAll('.spread')].map(s =>
    [...s.querySelectorAll('img:not([data-missing])')].filter(img => img.naturalWidth === 0).map(img => img.getAttribute('src')));
}"""


def _ranges(ns: list[int]) -> str:
    parts, start = [], None
    for k, n in enumerate(ns):
        if start is None:
            start = n
        if k + 1 == len(ns) or ns[k + 1] != n + 1:
            parts.append(f"{start}–{n}" if n > start else f"{n}")
            start = None
    return ", ".join(parts)


def _names(things: list[str]) -> str:
    blocks = sorted(int(t) for t in things if t.isdigit())
    return ", ".join(([f"block{'s' if len(blocks) > 1 else ''} {_ranges(blocks)}"] if blocks else [])
                     + [t for t in things if not t.isdigit()])


def _words(el) -> str:
    return " ".join(el.text_content().split())


def _source_texts(path: Path) -> dict[int, str]:
    """Each source block's words, to catch a placed block whose text differs from what was captured."""
    if not path.exists() or not path.read_text().strip():
        return {}
    return {int(el.get("data-b")): _words(el) for el in lxml.html.fragments_fromstring(path.read_text())
            if not isinstance(el, str) and el.get("data-b")}


def placement_problems(index_html: str, items_dir: Path) -> list[str]:
    doc = lxml.html.document_fromstring(index_html or "<p></p>")
    on_spreads = doc.xpath('//*[contains(concat(" ", normalize-space(@class), " "), " spread ")]//*[@data-src][@data-b]')
    placed = Counter((el.get("data-src"), int(el.get("data-b"))) for el in on_spreads)
    spreads = set(doc.xpath('//*[contains(concat(" ", normalize-space(@class), " "), " spread ")]/@data-item'))
    metas = [json.loads(p.read_text()) for p in sorted(items_dir.glob("*/meta.json"))]
    problems = []
    for m in metas:
        if m.get("status") != "ok":
            continue
        slug, n = m["slug"], int(m.get("blocks", 0))
        missing = [b for b in range(1, n + 1) if placed[(slug, b)] == 0]
        if missing:
            problems.append(f"{slug}: block{'s' if len(missing) > 1 else ''} {_ranges(missing)} missing")
        for b in range(1, n + 1):
            if placed[(slug, b)] > 1:
                problems.append(f"{slug}: block {b} placed {placed[(slug, b)]} times")
        source = _source_texts(items_dir / slug / "source.html")
        altered = sorted({int(el.get("data-b")) for el in on_spreads if el.get("data-src") == slug
                          and source.get(int(el.get("data-b")), _words(el)) != _words(el)})
        problems += [f"{slug}: block {b} altered" for b in altered]
    problems += [f"{m['slug']}: no spread" for m in metas if m["slug"] not in spreads]
    return problems


def render_problems(index: Path, proofs_dir: Path | None = None) -> list[str]:
    from playwright.sync_api import sync_playwright
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        page.goto(index.resolve().as_uri(), wait_until="load")
        page.add_style_tag(content=ONE_AT_A_TIME)
        broken = page.evaluate(IMAGES_JS)
        spreads = page.query_selector_all(".spread")
        if proofs_dir:
            proofs_dir.mkdir(parents=True, exist_ok=True)
        for i, el in enumerate(spreads):
            name = f"spread {i + 1} ({el.get_attribute('data-item') or '?'})"
            el.evaluate("s => { document.querySelectorAll('.__check').forEach(x => x.classList.remove('__check'));"
                        " s.classList.add('__check'); }")
            m = page.evaluate(MEASURE_JS, i)
            if m["over"] > 1:
                problems.append(f"{name}: overflows by {m['over']}px")
            problems += [f"{name}: block {b} is hidden" for b in m["hidden"]]
            problems += [f"{name}: {f} is faked by the browser (that weight or style isn't loaded)" for f in m["faked"]]
            problems += [f"{name}: broken image {src}" for src in broken[i]]
            if m["cross"]:
                problems.append(f"{name}: crosses the gutter, cut in two in the PDF: {_names(m['cross'])}")
            if m["near"]:
                problems.append(f"{name}: text within 60px of the gutter: {_names(m['near'])}")
            if proofs_dir:
                el.screenshot(path=str(proofs_dir / f"{i + 1:02}.png"))
        browser.close()
    return problems


def check(issue_dir: Path, shots: bool = False) -> list[str]:
    index = issue_dir / "index.html"
    if not index.exists():
        return ["index.html missing: run `python -m magazine assemble` first"]
    return (placement_problems(index.read_text(), issue_dir / "items")
            + render_problems(index, issue_dir / "proofs" if shots else None))
