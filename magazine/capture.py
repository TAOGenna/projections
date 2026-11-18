"""Capturing each saved link into items/<slug>/: full text as numbered blocks, images, style and a screenshot."""
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import lxml.html
import trafilatura
from lxml import etree

from magazine.inbox import Entry, slug_for
from magazine.source import (download, localize_images, number_blocks, protect_code, protect_headings,
                             protect_images, protect_math, restore_headings, restore_math)

BLOCKED = re.compile(r"just a moment|attention required|enable javascript|access denied|verify you are human", re.I)

STYLE_JS = """() => {
  const hex = c => { const m = c.match(/[\\d.]+/g); if (!m || (m.length === 4 && +m[3] === 0)) return null;
    return '#' + m.slice(0, 3).map(v => Math.round(+v).toString(16).padStart(2, '0')).join(''); };
  const named = ['body', 'h1', 'h2', 'a'].map(s => document.querySelector(s)).filter(Boolean);
  const big = [...document.querySelectorAll('body *')]
    .map(e => [e, e.getBoundingClientRect()])
    .filter(([e, r]) => r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden')
    .sort((a, b) => b[1].width * b[1].height - a[1].width * a[1].height).slice(0, 5).map(x => x[0]);
  const palette = [];
  for (const e of [...named, ...big]) { const s = getComputedStyle(e);
    for (const c of [s.color, s.backgroundColor]) { const h = hex(c); if (h && !palette.includes(h)) palette.push(h); } }
  const fonts = [];
  for (const sel of ['body', 'h1', 'code']) { const e = document.querySelector(sel);
    if (e) { const f = getComputedStyle(e).fontFamily; if (!fonts.includes(f)) fonts.push(f); } }
  return {palette, fonts};
}"""

SCROLL_JS = """async () => {
  for (let i = 0, y = 0; i < 80 && y < document.body.scrollHeight; i++, y += 800) {
    window.scrollTo(0, y); await new Promise(r => setTimeout(r, 150)); }
  window.scrollTo(0, 0);
}"""


def kind_of(url: str) -> Literal["video", "github", "arxiv", "pdf", "markdown", "html"]:
    u = urlparse(url)
    if u.scheme == "file" or u.path.lower().endswith((".md", ".markdown")):
        return "pdf" if u.path.lower().endswith(".pdf") else "markdown"
    host = (u.hostname or "").removeprefix("www.").removeprefix("m.")
    parts = [p for p in u.path.split("/") if p]
    if host == "youtu.be" or (host == "youtube.com" and parts[:1] in (["watch"], ["shorts"], ["live"])) \
            or (host == "vimeo.com" and parts[:1] and parts[0].isdigit()):
        return "video"
    if host == "github.com" and len(parts) == 2:
        return "github"
    if host.endswith("arxiv.org") and parts[:1] in (["abs"], ["pdf"], ["html"]):
        return "arxiv"
    if u.path.lower().endswith(".pdf"):
        return "pdf"
    return "html"


def looks_blocked(title: str, text: str) -> bool:
    """A bot wall or an empty shell: few words, or a wall's phrase in the title or on a short page."""
    words = len(text.split())
    return words < 80 or bool(BLOCKED.search(title)) or (words < 300 and bool(BLOCKED.search(text)))


def _body(html: str) -> str:
    body = lxml.html.document_fromstring(html).find("body")
    if body is None:
        return html
    return (body.text or "") + "".join(lxml.html.tostring(c, encoding="unicode") for c in body)


def finish(item_dir: Path, fragment: str, base_url: str | None, title: str, check_blocked: bool = True) -> dict:
    """Shared tail of every capturer: local images (unless already local), numbered blocks, source.html, blocked check."""
    slug = item_dir.name
    if base_url:
        fragment = localize_images(fragment, base_url, item_dir / "img", f"items/{slug}/img/")
    numbered, n = number_blocks(fragment)
    (item_dir / "source.html").write_text(numbered)
    text = lxml.html.fragment_fromstring(numbered or "<p></p>", create_parent="div").text_content()
    if n == 0:
        return {"blocks": 0, "status": "unreadable", "reason": "nothing to read"}
    if check_blocked and looks_blocked(title, text):  # only web pages can be bot walls
        return {"blocks": n, "status": "unreadable", "reason": "blocked or empty page"}
    return {"blocks": n}


def _class(name: str) -> str:
    return f'contains(concat(" ", normalize-space(@class), " "), " {name} ")'


SITE_CONTAINERS = {"codeforces.com": f"//div[{_class('problem-statement')}]", "atcoder.jp": "//*[@id='task-statement']"}


def site_fragment(html: str, url: str) -> str | None:
    """Sites whose statements the extractor mangles (contest problems): take the statement container whole,
    with its div-titles as real headings and every other wrapper unwrapped into blocks."""
    xpath = SITE_CONTAINERS.get((urlparse(url).hostname or "").removeprefix("www."))
    if not xpath:
        return None
    found = lxml.html.document_fromstring(html).xpath(xpath)
    if not found:
        return None
    box = found[0]
    for t in box.xpath(f".//div[{_class('input')} or {_class('output')}]/div[{_class('title')}]"):
        t.tag = "h3"
    for t in box.xpath(f".//div[{_class('section-title')}]"):
        t.tag = "h2"
    for t in box.xpath(f".//div[{_class('header')}]/div[{_class('title')}]"):
        t.tag = "h1"
    for t in box.xpath(f".//div[{_class('time-limit')} or {_class('memory-limit')} or {_class('input-file')} or {_class('output-file')}]"):
        t.tag = "p"
        for prop in t.xpath(f".//div[{_class('property-title')}]"):
            prop.tag, prop.tail = "span", " " + (prop.tail or "")
    for el in box.xpath(".//*[self::h1 or self::h2 or self::h3]"):
        el.attrib.clear()
    for d in box.xpath(".//div"):
        d.drop_tag()
    return (box.text or "") + "".join(lxml.html.tostring(c, encoding="unicode") for c in box)


# what a page marks as its own chrome, not its content: section edit links, side and navigation boxes
CHROME = "//*[" + " or ".join(_class(c) for c in ("mw-editsection", "sidebar", "navbox", "noprint")) + "]"


def tidy(html: str) -> str:
    """Drops the page's own chrome, and makes an indented equation (a dd holding only math) a paragraph, not a
    list item."""
    doc = lxml.html.document_fromstring(html)
    for el in doc.xpath(CHROME):
        el.drop_tree()
    for dd in doc.xpath("//dl/dd"):
        if re.fullmatch(r"\s*(⟦m\d+⟧[\s.,;:]*)+", dd.text_content()):
            dd.tag = "p"
    for dl in doc.xpath("//dl[not(dt) and not(dd)]"):
        dl.drop_tag()
    return lxml.html.tostring(doc, encoding="unicode")


def extract_page(html: str, url: str) -> str:
    """The page's main content as an HTML fragment. Math, images, inline code and headings travel through
    extraction as text tokens and are restored after, so nothing the extractor doesn't understand is lost."""
    tables: dict[str, str] = {}
    html, t = protect_math(html)
    tables |= t
    html = tidy(html)
    html, t = protect_images(html, url)
    tables |= t
    html, t = protect_code(html)
    tables |= t
    whole = site_fragment(html, url)
    if whole is not None:
        return restore_math(whole, tables)
    body = trafilatura.extract(protect_headings(html), url=url, output_format="html", include_images=True,
                               include_tables=True, include_formatting=True, include_links=True,
                               with_metadata=False) or ""
    return restore_math(restore_headings(_body(body)), tables) if body else ""


SAFARI_READ = """
on run argv
  set u to item 1 of argv
  tell application "Safari"
    try
      tell front window to set t to make new tab with properties {URL:u}
    on error
      make new document with properties {URL:u}
      set t to current tab of front window
    end try
    repeat with i from 1 to 120
      delay 0.5
      try
        set s to source of t
        if s contains "</html>" and s does not contain "challenge-platform" and s does not contain "Just a moment" then
          close t
          return s
        end if
      end try
      if i is 16 then activate -- still walled after 8 s: bring Safari forward so its owner can pass the check
    end repeat
  end tell
  error "timeout"
end run
"""


def read_in_safari(url: str) -> str | None:
    """The page as the owner's own Safari shows it (their session, their cookies). Projections never solves a
    human check; if one appears, Safari comes forward and its owner passes it. macOS only."""
    if sys.platform != "darwin":
        return None
    try:
        p = subprocess.run(["osascript", "-e", SAFARI_READ, url], capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return p.stdout if p.returncode == 0 and "</html>" in p.stdout else None


MATHJAX = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"
TYPESET_JS = """async (src) => {
  window.MathJax = {tex: {inlineMath: [['$$$', '$$$']], displayMath: [['$$$$$$', '$$$$$$']]},
                    startup: {typeset: false}};
  await new Promise((ok, no) => { const s = document.createElement('script'); s.src = src;
    s.onload = ok; s.onerror = no; document.head.appendChild(s); });
  await MathJax.startup.promise;
  await MathJax.typesetPromise();
}"""


def without_mathjax(html: str) -> str:
    """Drop a page's own MathJax config and loader, so its TeX is typeset by ours (which gives MathML)."""
    html = re.sub(r'<script[^>]*type="text/x-mathjax-config"[^>]*>.*?</script>', "", html, flags=re.S | re.I)
    return re.sub(r'<script[^>]*src="[^"]*MathJax\.js[^"]*"[^>]*>\s*</script>', "", html, flags=re.S | re.I)


def needs_typesetting(html: str) -> bool:
    """Math still in its TeX source ($$$...$$$, as Codeforces statements hold it) and not yet rendered."""
    return "$$$" in html and "mjx-assistive-mml" not in html and "MJX_Assistive_MathML" not in html


def _with_base(html: str, url: str) -> str:
    base = f'<base href="{escape(url)}">'
    return re.sub(r"<head[^>]*>", lambda m: m.group(0) + base, html, count=1) if re.search(r"<head[^>]*>", html) else base + html


DRAWN_JS = """() => {
  const big = g => { const r = g.getBoundingClientRect(); return r.width >= 120 && r.height >= 80; };
  const figures = [...document.querySelectorAll('figure')].filter(f => !f.querySelector('img, video')
    && !f.parentElement.closest('figure') && [...f.querySelectorAll('svg, canvas, iframe')].some(big));
  const frames = [...document.querySelectorAll('iframe')].filter(f => !f.closest('figure') && big(f)
    && !/youtube|youtu\\.be|vimeo|giscus|utteranc|disqus/.test(f.src));
  return [...figures, ...frames].map((f, i) => (f.dataset.drawn = i));
}"""


def picture_drawn_figures(page, out: Path) -> None:
    """A figure the page draws with script (SVG, canvas) or embeds (a plot in an iframe) becomes a picture of
    itself, as it looks, at twice its size for print: extraction keeps images, and here the drawing is the figure.
    Videos stay videos; comment threads are left out."""
    for i in page.evaluate(DRAWN_JS):
        fig, path = page.locator(f'[data-drawn="{i}"]'), out / f"{i}.png"
        try:
            out.mkdir(exist_ok=True)
            fig.screenshot(path=str(path), timeout=10_000)
        except Exception:
            continue
        fig.evaluate("(f, src) => f.replaceWith(Object.assign(document.createElement('img'), {src}))", path.resolve().as_uri())


def capture_html(url: str, item_dir: Path, browser) -> dict:
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)  # figures shot sharp
    try:
        try:
            resp = page.goto(url, wait_until="networkidle", timeout=45_000)
        except Exception as e:  # pages that never go quiet: keep what loaded
            if "Timeout" not in type(e).__name__:
                raise
            resp = None
            page.wait_for_load_state("load", timeout=15_000)
        via = ""
        if resp is not None and resp.status >= 400:  # an error, or a human check served with one
            walled = resp.status in (403, 429, 503) and bool(BLOCKED.search(page.content()[:50_000]))
        else:
            walled = bool(BLOCKED.search(page.title() or ""))
        if walled:  # a human check: read the page through its owner's Safari, then render that copy here
            source = read_in_safari(url)
            if source:
                if needs_typesetting(source):
                    source = without_mathjax(source)
                page.goto("about:blank")  # leave the check page: its security policy would block our scripts
                page.set_content(_with_base(source, url), wait_until="load", timeout=30_000)
                try:
                    page.wait_for_load_state("networkidle", timeout=15_000)
                except Exception:
                    pass
                via = "safari"
        elif resp is not None and resp.status >= 400:
            raise RuntimeError(f"HTTP {resp.status}")
        else:
            url = page.url  # after redirects: relative images resolve against where the page really is
        if needs_typesetting(page.content()):  # render the TeX the page left for its own script, as MathML
            try:
                page.evaluate(TYPESET_JS, MATHJAX)
            except Exception:
                pass
        page.evaluate(SCROLL_JS)
        page.screenshot(path=str(item_dir / "screenshot.png"), scale="css")
        style = page.evaluate(STYLE_JS)
        picture_drawn_figures(page, item_dir / "drawn")
        html = page.content()
    finally:
        page.close()
    md = trafilatura.extract_metadata(html, default_url=url)
    meta = {"title": (md and md.title) or "", "site": (md and md.sitename) or urlparse(url).hostname or "",
            "author": (md and md.author) or "", "date": (md and md.date) or "",
            "palette": style["palette"], "fonts": style["fonts"],
            "screenshot": f"items/{item_dir.name}/screenshot.png"}
    meta.update(finish(item_dir, extract_page(html, url), url, meta["title"]))
    shutil.rmtree(item_dir / "drawn", ignore_errors=True)  # finish() copied them into img/
    if via:
        meta["via"] = via
    elif walled:
        meta.update(status="unreadable", reason="a human check, and Safari couldn't read the page")
    return meta


def arxiv_id(url: str) -> str | None:
    m = re.search(r"arxiv\.org/(?:abs|pdf|html)/([^?#]+?)(?:\.pdf)?/?(?:[?#]|$)", url)
    return m.group(1) if m else None


def capture_arxiv(url: str, item_dir: Path, browser) -> dict:
    aid = arxiv_id(url)
    try:
        meta = capture_html(f"https://arxiv.org/html/{aid}", item_dir, browser)
        if meta.get("status") != "unreadable":
            return meta | {"site": "arxiv.org"}
    except Exception:
        pass  # no HTML version: the PDF is the paper
    shutil.rmtree(item_dir / "img", ignore_errors=True)
    meta = capture_pdf(f"https://arxiv.org/pdf/{aid}", item_dir, browser) | {"site": "arxiv.org"}
    try:  # the PDF's own metadata is often a template's ("AAAI Proceedings Template"); arXiv knows better
        meta |= arxiv_atom_meta(download(f"https://export.arxiv.org/api/query?id_list={aid}").decode())
    except Exception:
        pass
    return meta


def is_heading(p: str) -> bool:
    return (0 < len(p.split()) <= 8 and p[-1] not in ".,;:-" and (p[0].isupper() or p[0].isdigit())
            and "@" not in p and bool(re.search(r"[A-Za-z]{3}", p)))


def pdf_paragraphs(text: str) -> list[str]:
    out = []
    for page in text.split("\x0c"):
        lines = page.strip().splitlines()
        if lines and lines[0].strip().isdigit():
            lines = lines[1:]
        if lines and lines[-1].strip().isdigit():
            lines = lines[:-1]
        for chunk in re.split(r"\n\s*\n", "\n".join(lines)):
            lines_ = [l for l in (l.strip() for l in chunk.splitlines()) if l]
            # a heading sits on its own line straight above its text: short, unpunctuated, followed by a capital
            if len(lines_) > 1 and is_heading(lines_[0]) and lines_[1][0].isupper():
                out.append(lines_.pop(0))
            para = ""
            for line in lines_:
                if para.endswith("-"):
                    para = para[:-1] + line
                else:
                    para = f"{para} {line}" if para else line
            if para:
                out.append(para)
    return out


def arxiv_atom_meta(xml: str) -> dict:
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entry = etree.fromstring(xml.encode()).find("a:entry", ns)
    return {"title": " ".join(entry.findtext("a:title", "", ns).split()),
            "author": ", ".join(n.text for n in entry.findall("a:author/a:name", ns)),
            "date": entry.findtext("a:published", "", ns)[:10]}


def _run(*cmd) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


MATH_CHARS = re.compile("[\U0001D400-\U0001D7FF∑∏∫√∂∈∉≤≥≠±×→∞∇]")
EQ_NUMBER = re.compile(r"^\(\d+[a-z]?\)$")


def math_like(s: str) -> bool:
    """A piece of a display equation as PDF text gives it: math letters, hardly any prose words."""
    return bool(MATH_CHARS.search(s)) and len(re.findall(r"[A-Za-z]{3,}", s)) <= 2


def equation_runs(paras: list[str]) -> list[tuple[int, int]]:
    """Index ranges of consecutive paragraphs that are pieces of display equations (or their numbers)."""
    runs, start = [], None
    for i, p in enumerate(paras + [""]):
        if p and (math_like(p) or EQ_NUMBER.match(p.strip())):
            start = i if start is None else start
        elif start is not None:
            runs.append((start, i - 1))
            start = None
    return runs


def equation_box(lines: list[tuple], texts: list[str], page_width: float | None = None):
    """The box (x0, y0, x1, y1) of the display equation whose PDF lines include `texts`: grown from the first
    matching line through vertically adjacent math lines in the same column. None if nothing matches."""
    norm = lambda t: "".join(t.split())
    want = {norm(t) for t in texts}
    seeds = [l for l in lines if norm(l[0]) in want]
    seeds.sort(key=lambda l: not EQ_NUMBER.match(l[0].strip()))  # an equation's number is unique on its page
    if not seeds:
        return None
    width = page_width or max(l[3] for l in lines)
    mid = width / 2
    two_columns = any(l[3] < mid for l in lines) and any(l[1] > mid for l in lines)
    side = lambda l: (l[1] + l[3]) / 2 > mid
    x0, y0, x1, y1 = seeds[0][1:]
    grown = True
    while grown:
        grown = False
        for t, a, b, c, d in lines:
            if (a, b, c, d) == (x0, y0, x1, y1) or (x0 <= a and c <= x1 and y0 <= b and d <= y1):
                continue
            if not (math_like(t) or EQ_NUMBER.match(t.strip()) or norm(t) in want):
                continue
            if two_columns and side((t, a, b, c, d)) != side(seeds[0]):
                continue
            if b - y1 <= 14 and y0 - d <= 14:
                x0, y0, x1, y1 = min(x0, a), min(y0, b), max(x1, c), max(y1, d)
                grown = True
    return (x0, y0, x1, y1)


def strip_math_tail(p: str) -> str:
    """Drop an equation's first pieces that PDF text glued onto the end of the paragraph before it."""
    tokens = p.split()
    k = len(tokens)
    while k and not re.search(r"[A-Za-z]{2,}", tokens[k - 1]):
        k -= 1
    tail = tokens[k:]
    return " ".join(tokens[:k]) if any(MATH_CHARS.search(t) for t in tail) else p


def _pdf_lines(pdf: Path) -> dict[int, tuple[float, list[tuple]]]:
    return pdf_lines_from(subprocess.run(["pdftotext", "-bbox-layout", str(pdf), "-"], check=True,
                                         capture_output=True).stdout)


def pdf_lines_from(xhtml: bytes) -> dict[int, tuple[float, list[tuple]]]:
    """Each page's width and its text lines with their boxes, from pdftotext's layout output (UTF-8)."""
    doc = lxml.html.fromstring(xhtml, parser=lxml.html.HTMLParser(encoding="utf-8"))
    out = {}
    for n, page in enumerate(doc.iter("page"), 1):
        out[n] = (float(page.get("width")), [(" ".join(w.text_content() for w in line.iter("word")),
                   *(float(line.get(k)) for k in ("xmin", "ymin", "xmax", "ymax"))) for line in page.iter("line")])
    return out


def _pdf_page_blocks(pdf: Path, n: int, paras: list[str], geometry, img_dir: Path, slug: str) -> list[str]:
    """A page's paragraphs as blocks. Display equations, which PDF text scatters into pieces, become an image
    cropped from the page where their box can be found."""
    runs = dict(equation_runs(paras))
    blocks, i = [], 0
    while i < len(paras):
        if i in runs and geometry:
            end = runs[i]
            box = equation_box(geometry[1], paras[i:end + 1], geometry[0])
            if box and box[3] - box[1] < 300:
                x0, y0, x1, y1 = box
                name, dpi = f"eq-{n:03}-{i:03}", 200
                px = lambda v: str(int(v * dpi / 72))
                _run("pdftoppm", "-png", "-r", str(dpi), "-f", str(n), "-l", str(n), "-x", px(x0 - 4), "-y", px(y0 - 4),
                     "-W", px(x1 - x0 + 8), "-H", px(y1 - y0 + 8), "-singlefile", str(pdf), str(img_dir / name))
                if i > 0 and blocks and blocks[-1].startswith("<p>"):  # the image shows what the tail garbled
                    blocks[-1] = f"<p>{escape(strip_math_tail(paras[i - 1]))}</p>"
                number = next((p for p in paras[i:end + 1] if EQ_NUMBER.match(p.strip())), "")
                width = int((x1 - x0 + 8) * 1.35)  # the PDF's 10pt type at the issue's text size
                blocks.append(f'<figure class="equation"><img src="items/{slug}/img/{name}.png" width="{width}" '
                              f'alt="equation {escape(number)}"></figure>')
                i = end + 1
                continue
        p = paras[i]
        blocks.append(f"<h2>{escape(p)}</h2>" if is_heading(p) else f"<p>{escape(p)}</p>")
        i += 1
    return blocks


def capture_pdf(url: str, item_dir: Path, browser) -> dict:
    slug, pdf = item_dir.name, item_dir / "source.pdf"
    data = download(url)
    if not data.startswith(b"%PDF"):
        raise RuntimeError("not a PDF")
    pdf.write_bytes(data)
    info = dict(re.findall(r"^(\w+):\s*(.*)$", _run("pdfinfo", str(pdf)), re.M))
    pages = _run("pdftotext", "-enc", "UTF-8", str(pdf), "-").split("\x0c")
    geometry = _pdf_lines(pdf)
    img_dir = item_dir / "img"
    img_dir.mkdir(exist_ok=True)
    keep = set()  # (page, num) of real figures, not icons or masks
    for row in _run("pdfimages", "-list", str(pdf)).splitlines()[2:]:
        f = row.split()
        if len(f) > 4 and f[2] == "image" and int(f[3]) >= 150 and int(f[4]) >= 150:
            keep.add((int(f[0]), int(f[1])))
    _run("pdfimages", "-png", "-p", str(pdf), str(img_dir / "p"))
    figures: dict[int, list[str]] = {}
    for png in sorted(img_dir.glob("p-*-*.png")):
        _, page, num = png.stem.split("-")
        if (int(page), int(num)) in keep:
            figures.setdefault(int(page), []).append(png.name)
        else:
            png.unlink()
    _run("pdftoppm", "-png", "-r", "110", "-f", "1", "-l", "1", "-singlefile", str(pdf), str(item_dir / "screenshot"))
    blocks = []
    for n, text in enumerate(pages, 1):
        blocks += _pdf_page_blocks(pdf, n, pdf_paragraphs(text), geometry.get(n), img_dir, slug)
        blocks += [f'<figure><img src="items/{slug}/img/{name}"></figure>' for name in figures.get(n, [])]
    paras = [p for t in pages for p in pdf_paragraphs(t)]
    title = info.get("Title", "").strip() or (paras[0][:120] if paras else "")
    meta = {"title": title, "author": info.get("Author", "").strip(), "site": urlparse(url).hostname or "",
            "screenshot": f"items/{slug}/screenshot.png"}
    return meta | finish(item_dir, "".join(blocks), None, title, check_blocked=False)


def readme_base(owner: str, repo: str, branch: str) -> str:
    # github.com/…/raw/… serves both the README's relative and root-relative image paths
    return f"https://github.com/{owner}/{repo}/raw/{branch}/"


def _github(path: str, accept: str) -> bytes:
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": accept, "User-Agent": "magazine"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def capture_github(url: str, item_dir: Path, browser) -> dict:
    owner, repo = [p for p in urlparse(url).path.split("/") if p][:2]
    info = json.loads(_github(f"/repos/{owner}/{repo}", "application/vnd.github+json"))
    readme = lxml.html.fragment_fromstring(
        _github(f"/repos/{owner}/{repo}/readme", "application/vnd.github.html").decode(), create_parent="div")
    body = (readme.xpath('.//*[contains(@class, "markdown-body")]') or [readme])[0]
    for a in body.xpath('.//a[contains(@class, "anchor")]'):
        a.drop_tree()  # the hover link icons beside headings
    for d in body.xpath('.//div[contains(@class, "markdown-heading")]'):
        d.drop_tag()  # keep the heading itself as the block
    inner = (body.text or "") + "".join(lxml.html.tostring(c, encoding="unicode") for c in body)
    stars = f"★ {info.get('stargazers_count', 0):,}"
    head = f'<p class="repo-meta">{escape(info.get("description") or "")} · {stars} · {escape(url)}</p>'
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    try:
        page.goto(url, wait_until="load", timeout=45_000)
        page.screenshot(path=str(item_dir / "screenshot.png"), scale="css")
        style = page.evaluate(STYLE_JS)
    finally:
        page.close()
    title = f"{owner}/{repo}"
    meta = {"title": title, "site": "github.com", "author": owner, "palette": style["palette"],
            "fonts": style["fonts"], "screenshot": f"items/{item_dir.name}/screenshot.png"}
    return meta | finish(item_dir, head + inner, readme_base(owner, repo, info["default_branch"]), title,
                         check_blocked=False)


def _seconds(stamp: str) -> float:
    parts = [float(p) for p in stamp.split(":")]
    return sum(p * 60 ** i for i, p in enumerate(reversed(parts)))


def vtt_to_paragraphs(vtt: str) -> list[str]:
    paras, words, last_line, last_end = [], [], None, None
    for cue in re.split(r"\n\s*\n", vtt):
        lines = cue.strip().splitlines()
        timing = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if timing is None:
            continue
        start, end = (_seconds(t.split()[0]) for t in lines[timing].split("-->"))
        if words and (last_end is not None and start - last_end > 2 or len(words) >= 80):
            paras.append(" ".join(words))
            words = []
        for line in lines[timing + 1:]:
            line = re.sub(r"<[^>]+>", "", line).strip()
            if line and line != last_line:
                words += line.split()
                last_line = line
        last_end = end
    if words:
        paras.append(" ".join(words))
    return paras


def pick_subtitle(names: list[str], language: str | None) -> str | None:
    """The track in the language spoken, never one YouTube machine-translated into another language."""
    lang = lambda n: n.split(".")[-2]  # v.<lang>.vtt
    for n in names:
        if language and lang(n) in (language, f"{language}-orig"):
            return n
    for n in names:
        if lang(n).endswith("-orig"):
            return n
    return min(names, key=lambda n: (not lang(n).startswith("en"), n), default=None)


def capture_video(url: str, item_dir: Path, browser) -> dict:
    run = subprocess.run(["yt-dlp", "--skip-download", "--write-info-json", "--write-auto-subs", "--write-subs",
                          "--sub-langs", "en.*,es.*,.*-orig", "--sub-format", "vtt", "--write-thumbnail",
                          "--convert-thumbnails", "png", "-o", str(item_dir / "v"), url],
                         capture_output=True, text=True)
    if not (item_dir / "v.info.json").exists():  # a subtitle hiccup alone shouldn't lose the video
        raise RuntimeError("yt-dlp: " + (run.stderr.strip().splitlines() or ["failed"])[-1])
    info = json.loads((item_dir / "v.info.json").read_text())
    shot = ""
    for thumb in item_dir.glob("v.png"):
        thumb.rename(item_dir / "screenshot.png")
        shot = f"items/{item_dir.name}/screenshot.png"
    meta = {"title": info.get("title", ""), "author": info.get("uploader") or info.get("channel") or "",
            "date": info.get("upload_date", ""), "site": urlparse(url).hostname or "", "screenshot": shot}
    sub = pick_subtitle(sorted(p.name for p in item_dir.glob("v.*.vtt")), info.get("language"))
    if not sub:
        return meta | {"status": "unreadable", "reason": "no transcript"}
    paras = vtt_to_paragraphs((item_dir / sub).read_text())
    return meta | finish(item_dir, "".join(f"<p>{escape(p)}</p>" for p in paras), None, meta["title"],
                         check_blocked=False)


# code first, so a $ inside code stays code; then display math (a callout's "> " prefixes inside it are stripped); then
# inline math, Pandoc's rule: no space inside either $, no digit right after the closing one (so "$5 and $6" is prose)
MD_MATH = re.compile(r"(```.*?```|`[^`\n]*`)|\$\$(.+?)\$\$|(?<![\\$\w])\$(?=\S)([^$\n]+?)(?<=\S)\$(?![\d$])", re.S)
CALLOUT = re.compile(r"^\s*\[!(\w+)\][+-]?\s*")
CALLOUT_HEAD = re.compile(r"(?m)^(\s*>\s*\[!\w+\][+-]?.*)\n(\s*>)")  # gets an empty quoted line: the title is its own <p>


def markdown_fragment(text: str) -> tuple[str, str, list[tuple[str, bool]]]:
    """A note's Markdown (CommonMark and GitHub's tables, as Obsidian writes it) as HTML: its title (the first `# `
    line, dropped from the body), the body, and its TeX, each formula left as ⟦mN⟧ for MathJax to typeset into MathML."""
    from markdown_it import MarkdownIt

    maths: list[tuple[str, bool]] = []

    def keep(m: re.Match) -> str:
        if m.group(1):
            return m.group(1)
        tex, display = (re.sub(r"(?m)^\s*>\s?", "", m.group(2)), True) if m.group(2) else (m.group(3), False)
        maths.append((tex.strip(), display))
        return f"⟦m{len(maths) - 1}⟧"

    title = ""
    if m := re.search(r"(?m)^# (.+)\n?", text):
        title, text = m.group(1).strip(), text[:m.start()] + text[m.end():]
    text = re.sub(r"!\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", lambda m: f"![]({m.group(1).replace(' ', '%20')})", text)  # embeds
    text = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]", r"\1", text)  # wiki links read as their text
    text = CALLOUT_HEAD.sub(r"\1\n\2\n\2", MD_MATH.sub(keep, text))
    html = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"]).render(text)
    root = lxml.html.fragment_fromstring(html or "<p></p>", create_parent="div")
    for q in root.xpath("./blockquote"):  # > [!kind] Title: a callout, its kind kept for the designer
        first = q.find("p")
        if first is not None and (m := CALLOUT.match(first.text or "")):
            q.set("class", "callout")
            q.set("data-callout", m.group(1).lower())
            first.text = first.text[m.end():]
            first.set("class", "callout-title")
    for li in root.iter("li"):  # a task, "- [ ] …": the box is markup, drawn by the chapter's style
        holder = li.find("p") if li.find("p") is not None and not (li.text or "").strip() else li
        if m := re.match(r"\s*\[([ xX])\]\s+", holder.text or ""):
            holder.text = holder.text[m.end():]
            li.set("class", "task done" if m.group(1) in "xX" else "task")
    for lst in root.xpath("./ul | ./ol"):  # one block per item: a block never breaks across pages, a long list must
        start = int(lst.get("start", "1"))
        for k, li in enumerate(lst.findall("li")):
            one = lxml.html.Element(lst.tag, {"start": str(start + k)} if lst.tag == "ol" and start + k > 1 else {})
            one.append(li)
            lst.addprevious(one)
        lst.drop_tree()
    body = (root.text or "") + "".join(lxml.html.tostring(c, encoding="unicode") for c in root)
    return title, body, maths


def typeset(maths: list[tuple[str, bool]], browser) -> list[str]:
    """TeX to MathML with MathJax, the way capture_html typesets a page that only had TeX."""
    if not maths:
        return []
    page = browser.new_page()
    try:
        page.set_content(f'<script src="{MATHJAX}"></script>', wait_until="networkidle")
        page.wait_for_function("window.MathJax && MathJax.startup && MathJax.startup.promise")
        page.evaluate("MathJax.startup.promise")
        out = page.evaluate("""ms => ms.map(([tex, display]) => {
          try { return MathJax.tex2mml(tex, {display}); }
          catch (e) { return '<math><merror><mtext>' + tex.replace(/&/g, '&amp;').replace(/</g, '&lt;') + '</mtext></merror></math>'; }
        })""", [list(m) for m in maths])
    finally:
        page.close()
    return [re.sub(r"\s*\n\s*", "", m) for m in out]


def capture_markdown(url: str, item_dir: Path, browser) -> dict:
    """A Markdown note, on disk (file://) or on the web: its images sit beside it, relative to the file."""
    text = download(url).decode("utf-8", errors="replace")
    title, body, maths = markdown_fragment(text)
    mml = typeset(maths, browser)
    body = re.sub(r"⟦m(\d+)⟧", lambda m: mml[int(m.group(1))], body)
    u = urlparse(url)
    path = Path(urllib.request.url2pathname(u.path))
    meta = {"title": title or path.stem, "site": "your notes" if u.scheme == "file" else u.hostname or "",
            "date": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d") if u.scheme == "file" else ""}
    return meta | finish(item_dir, body, url, meta["title"], check_blocked=False)


CAPTURERS = {"html": capture_html, "arxiv": capture_arxiv, "pdf": capture_pdf, "github": capture_github,
             "video": capture_video, "markdown": capture_markdown}


def capture(entry: Entry, item_dir: Path, browser) -> dict:
    kind = kind_of(entry.url)
    meta = {"url": entry.url, "note": entry.note, "slug": item_dir.name, "kind": kind, "status": "ok", "reason": "",
            "title": "", "site": "", "author": "", "date": "", "blocks": 0, "palette": [], "fonts": [],
            "screenshot": ""}
    item_dir.mkdir(parents=True, exist_ok=True)
    try:
        meta.update(CAPTURERS.get(kind, capture_html)(entry.url, item_dir, browser))
    except Exception as e:
        meta.update(status="unreadable", reason=f"{type(e).__name__}: {e}".splitlines()[0][:200])
    (item_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return meta


class _LazyBrowser:
    """Launches Chromium on first use, so runs with nothing new to capture never start a browser."""

    def __init__(self):
        self._pw = self._browser = None

    def __getattr__(self, name):
        if self._browser is None:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch()
        return getattr(self._browser, name)

    def close(self):
        if self._browser is not None:
            self._browser.close()
            self._pw.stop()


def recapture(issue_dir: Path, slug: str, url: str) -> dict:
    """Capture `url` into an existing item's folder, remembering the link as saved (e.g. a blog's front page)."""
    item_dir = issue_dir / "items" / slug
    old = json.loads((item_dir / "meta.json").read_text())
    shutil.rmtree(item_dir)
    browser = _LazyBrowser()
    try:
        meta = capture(Entry(url, old.get("note", "")), item_dir, browser)
    finally:
        browser.close()
    meta["saved_url"] = old.get("saved_url") or old["url"]
    (item_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return meta


def capture_all(entries: list[Entry], issue_dir: Path, force: bool = False) -> list[dict]:
    items = issue_dir / "items"
    items.mkdir(parents=True, exist_ok=True)
    issue_json = issue_dir / "issue.json"
    if not issue_json.exists():
        number = len(list(issue_dir.parent.glob("*/issue.json"))) + 1
        issue_json.write_text(json.dumps({"number": number, "month": issue_dir.name}))
    existing = {}  # the link as saved -> its folder, so each link keeps its own folder whatever the inbox order
    for mp in sorted(items.glob("*/meta.json")):
        m = json.loads(mp.read_text())
        existing.setdefault(m.get("saved_url") or m.get("url"), mp.parent.name)
    taken, metas, browser = set(existing.values()), [], _LazyBrowser()
    try:
        for e in entries:
            slug = existing.get(e.url) or slug_for(e.url, taken)
            taken.add(slug)
            meta_path = items / slug / "meta.json"
            old = json.loads(meta_path.read_text()) if meta_path.exists() else None
            if old and old.get("status", "ok") == "ok" and not force:
                metas.append(old)
                continue
            # retry unreadable items too; a resolved front page is captured again from the post it pointed to
            saved = old.get("saved_url") if old else None
            meta = capture(Entry(old["url"] if saved else e.url, e.note), items / slug, browser)
            if saved:
                meta["saved_url"] = saved
                meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
            metas.append(meta)
    finally:
        browser.close()
    return metas
