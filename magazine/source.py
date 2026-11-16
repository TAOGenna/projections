"""Turning captured HTML into numbered blocks, with local images and math that survives extraction."""
import re
from html import escape
import urllib.request
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse

import lxml.html
from lxml import etree

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
BLOCK = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "ul", "ol", "dl", "table", "figure", "blockquote",
         "div", "section", "article", "aside", "header", "footer", "details", "hr", "math", "svg", "video", "iframe"}
CONTENT = ".//img|.//svg|.//math|.//video|.//iframe|.//table|self::img|self::svg|self::math|self::video|self::iframe"
IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".avif"}


def _root(fragment_html: str):
    return lxml.html.fragment_fromstring(fragment_html, create_parent="div")


def _inner(root) -> str:
    return (root.text or "") + "".join(lxml.html.tostring(c, encoding="unicode") for c in root)


def _add_text(el, text: str) -> None:
    if len(el):
        el[-1].tail = (el[-1].tail or "") + text
    else:
        el.text = (el.text or "") + text


def number_blocks(fragment_html: str) -> tuple[str, int]:
    if not fragment_html.strip():
        return "", 0
    root = _root(fragment_html)
    blocks, run = [], None

    def loose():
        nonlocal run
        if run is None:
            run = etree.Element("p")
            blocks.append(run)
        return run

    if root.text and root.text.strip():
        _add_text(loose(), root.text)
    for child in list(root):
        tail, child.tail = child.tail, None
        if not isinstance(child.tag, str):  # comments, processing instructions
            pass
        elif child.tag in BLOCK:
            blocks.append(child)
            run = None
        else:
            loose().append(child)
        if tail and (tail.strip() or run is not None):
            _add_text(loose(), tail)
    kept = [b for b in blocks if "".join(b.itertext()).strip() or b.xpath(CONTENT)]
    out = []
    for i, b in enumerate(kept, 1):
        b.set("data-b", str(i))
        out.append(lxml.html.tostring(b, encoding="unicode"))
    return "\n".join(out), len(kept)


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _best_src(img) -> str | None:
    def scored(srcset: str):
        for cand in srcset.split(","):
            parts = cand.split()
            if not parts:
                continue
            d = parts[1] if len(parts) > 1 else "1x"
            try:
                yield float(d[:-1]), parts[0]
            except ValueError:
                yield 1.0, parts[0]
    options = []
    if img.get("srcset"):
        options.append(max(scored(img.get("srcset")), default=(0, None))[1])
    options += [img.get("data-src"), img.get("data-original"), img.get("src")]
    return next((u for u in options if u and not u.startswith("data:")), None)


def _ext(url: str, data: bytes) -> str:
    """The file's real type decides its extension: an SVG saved as .jpg never renders."""
    head = data[:64].lstrip()
    if head.startswith((b"<svg", b"<?xml")):
        return ".svg"
    for magic, ext in ((b"\x89PNG", ".png"), (b"\xff\xd8", ".jpg"), (b"GIF8", ".gif")):
        if data.startswith(magic):
            return ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    ext = Path(urlparse(url).path).suffix.lower()
    return ext if ext in IMG_EXT else ".jpg"


MAX_WIDTH = 2400  # the widest any image is ever shown (a full spread, 1600 px) at 2x, rounded up


def shrink(path: Path, max_width: int = MAX_WIDTH) -> None:
    """Keep an image no wider than it is ever shown: a 13,000 px figure costs a frozen frame to decode.
    Same file, same format, same transparency; anything Pillow can't read (SVG) is left as it is."""
    from PIL import Image
    try:
        with Image.open(path) as im:
            if im.width <= max_width or getattr(im, "is_animated", False):
                return
            fmt = im.format
            small = im.resize((max_width, max(1, round(im.height * max_width / im.width))), Image.LANCZOS)
    except Exception:
        return
    small.save(path, fmt, **({"optimize": True} if fmt == "PNG" else {"quality": 90} if fmt in ("JPEG", "WEBP") else {}))


def localize_images(fragment_html: str, base_url: str, img_dir: Path, rel_prefix: str,
                    fetch: Callable[[str], bytes] = download) -> str:
    root = _root(fragment_html)
    for source in root.xpath(".//picture/source"):
        source.drop_tree()  # a <source srcset> would win over the local src
    for n, img in enumerate(root.iter("img"), 1):
        url = _best_src(img)
        for attr in ("srcset", "sizes", "data-src", "data-original"):
            img.attrib.pop(attr, None)
        if not url:
            continue
        url = urljoin(base_url, url)
        try:
            data = fetch(url)
            name = f"{n:02}{_ext(url, data)}"
            img_dir.mkdir(parents=True, exist_ok=True)
            (img_dir / name).write_bytes(data)
            shrink(img_dir / name)
            img.set("src", rel_prefix + name)
        except Exception:
            img.set("src", url)
            img.set("data-missing", "1")
    return _inner(root)


def _has_class(*names: str) -> str:
    return " or ".join(f'contains(concat(" ", normalize-space(@class), " "), " {n} ")' for n in names)


# the MathML copy each renderer keeps for screen readers (MathJax 2, MathJax 3, KaTeX)
ASSISTIVE = f'//*[{_has_class("MJX_Assistive_MathML", "katex-mathml")}]//math|//mjx-assistive-mml//math'
# the visual copies (MathJax 2 HTML-CSS, CommonHTML and SVG; MathJax 3; KaTeX), removed so nothing is read twice
VISUAL = {"MathJax", "MathJax_Display", "MathJax_Preview", "MathJax_CHTML", "mjx-chtml", "MJXc-display",
          "MathJax_SVG", "MathJax_SVG_Display", "katex-html"}
RENDERED = f'//*[{_has_class(*VISUAL)}]|//mjx-container'
# wrappers that hold one whole formula: the token replaces the outermost of them
OUTER = {"MathJax", "MathJax_Display", "MathJax_CHTML", "mjx-chtml", "MJXc-display", "MathJax_SVG",
         "MathJax_SVG_Display", "katex", "katex-display"}


DISPLAY = {"MathJax_Display", "MJXc-display", "MathJax_SVG_Display", "katex-display"}


def _classes(el) -> set[str]:
    return set((el.get("class") or "").split())


def _replace_with_text(el, text: str) -> None:
    text += el.tail or ""
    prev, parent = el.getprevious(), el.getparent()
    if prev is not None:
        prev.tail = (prev.tail or "") + text
    else:
        parent.text = (parent.text or "") + text
    parent.remove(el)


class _Tokens:
    def __init__(self, letter: str):
        self.letter, self.table = letter, {}

    def add(self, html: str) -> str:
        token = f"⟦{self.letter}{len(self.table) + 1}⟧"
        self.table[token] = html
        return token


def protect_math(page_html: str) -> tuple[str, dict[str, str]]:
    """Replace each formula with a ⟦mN⟧ token that extraction keeps as text; the table holds its MathML."""
    doc = lxml.html.document_fromstring(page_html)
    body = doc.find("body")
    tokens = _Tokens("m")
    for math in doc.xpath(ASSISTIVE):
        if body not in math.iterancestors():
            continue  # already gone with an earlier formula's wrapper
        outer = math.getparent()
        for anc in math.iterancestors():
            if anc is body:
                break
            if anc.tag == "mjx-container" or OUTER & _classes(anc):
                outer = anc
        token = tokens.add(lxml.html.tostring(math, encoding="unicode", with_tail=False))
        if (outer.get("display") == "true" or DISPLAY & _classes(outer)) and outer.getparent().tag not in INLINE_PARENTS:
            p = lxml.html.Element("p")  # a displayed formula between paragraphs: its own block, not loose text
            p.text, p.tail = token, outer.tail
            outer.addprevious(p)
            outer.getparent().remove(outer)
        else:
            _replace_with_text(outer, token)
    # MathJax 2 without assistive MathML: the rendering is all that's left, so keep the source TeX instead
    for script in doc.xpath('//script[starts-with(@type, "math/tex")]'):
        prev = script.getprevious()
        if prev is not None and (prev.tag == "mjx-container" or VISUAL & _classes(prev)):
            tex = script.text_content().strip()
            shown = f"\\[{tex}\\]" if "display" in script.get("type", "") else f"\\({tex}\\)"
            _replace_with_text(prev, tokens.add(f'<span class="tex">{escape(shown)}</span>'))
    # Wikipedia: MathML in a hidden span beside a picture of the formula; keep the MathML, drop the picture
    for el in doc.xpath(f'//*[{_has_class("mwe-math-element")}]'):
        math = el.xpath(".//math")
        if math and el.getparent() is not None:
            _replace_with_text(el, tokens.add(lxml.html.tostring(math[0], encoding="unicode", with_tail=False)))
    # plain MathML (LaTeXML, arXiv's HTML papers, Wikipedia), lifted out of any hidden wrapper extraction would drop
    for math in doc.xpath("//body//math[not(ancestor::math)]"):
        outer = math
        while outer.getparent() is not None and "display:none" in (outer.getparent().get("style") or "").replace(" ", ""):
            outer = outer.getparent()
        _replace_with_text(outer, tokens.add(lxml.html.tostring(math, encoding="unicode", with_tail=False)))
    for el in doc.xpath(RENDERED):
        if el.getparent() is not None:
            el.drop_tree()
    for s in doc.xpath('//script[starts-with(@type, "math/tex")]'):
        s.drop_tree()
    return lxml.html.tostring(doc, encoding="unicode"), tokens.table


# the image files trafilatura recognises by name; anything else (svg, no extension) it drops
EXTRACTION_KEEPS = re.compile(r"\.(avif|bmp|gif|heic|jpe?g|png|webp)$", re.I)
INLINE_PARENTS = {"p", "figure", "a", "picture", "span", "li", "td", "th", "em", "strong", "b", "i"}


def protect_images(page_html: str, base_url: str) -> tuple[str, dict[str, str]]:
    """Replace each <img> and inline <svg> with a ⟦iN⟧ token, so extraction can't drop images it doesn't
    recognise (svg, extension-less, srcset-only). A bare image gets its own paragraph."""
    doc = lxml.html.document_fromstring(page_html)
    tokens = _Tokens("i")
    for el in doc.xpath("//body//img|//body//svg[not(ancestor::svg)]"):
        if el.getparent() is None:
            continue
        if el.tag == "img":
            src = _best_src(el) or el.get("src")
            if not src:
                el.drop_tree()
                continue
            src = src if src.startswith("data:") else urljoin(base_url, src)
            if not src.startswith("data:") and EXTRACTION_KEEPS.search(urlparse(src).path):
                # extraction keeps these itself; a token would read as a scrap of text in a link-heavy box
                alt = el.get("alt", "")
                el.attrib.clear()
                el.set("src", src)
                el.set("alt", alt)
                if el.getparent().tag not in INLINE_PARENTS:
                    wrap = lxml.html.Element("p")
                    el.addprevious(wrap)
                    wrap.tail, el.tail = el.tail, None
                    wrap.append(el)
                continue
            html = f'<img src="{escape(src)}" alt="{escape(el.get("alt", ""))}">'
        else:
            html = lxml.html.tostring(el, encoding="unicode", with_tail=False)
        target, link = el, el.getparent()
        if link.tag == "a" and len(link) == 1 and not link.text_content().strip():
            # an image that is the whole link: extraction drops link-only text, so the token carries the link
            html = f'<a href="{escape(urljoin(base_url, link.get("href", "")))}">{html}</a>'
            target = link
        token = tokens.add(html)
        if target.getparent().tag in INLINE_PARENTS:
            _replace_with_text(target, token)
        else:
            p = lxml.html.Element("p")
            p.text, p.tail = token, target.tail
            target.addprevious(p)
            target.getparent().remove(target)
    return lxml.html.tostring(doc, encoding="unicode"), tokens.table


def protect_code(page_html: str) -> tuple[str, dict[str, str]]:
    """Inline <code> (not inside <pre>) becomes a ⟦cN⟧ token: extraction turns it into a block otherwise."""
    doc = lxml.html.document_fromstring(page_html)
    tokens = _Tokens("c")
    for code in doc.xpath("//body//code[not(ancestor::pre)]"):
        _replace_with_text(code, tokens.add(lxml.html.tostring(code, encoding="unicode", with_tail=False)))
    return lxml.html.tostring(doc, encoding="unicode"), tokens.table


def protect_headings(page_html: str) -> str:
    """Turn each <h1>–<h6> into a <p> starting with a ⟦hN⟧ marker, which extraction keeps as text."""
    doc = lxml.html.document_fromstring(page_html)
    for h in doc.xpath("//body//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]"):
        h.text = f"⟦{h.tag}⟧" + (h.text or "")
        h.tag = "p"
        h.attrib.clear()
    return lxml.html.tostring(doc, encoding="unicode")


def restore_headings(html: str) -> str:
    html = re.sub(r"<p[^>]*>\s*⟦(h[1-6])⟧(.*?)</p>", r"<\1>\2</\1>", html, flags=re.S)
    return re.sub(r"⟦h[1-6]⟧", "", html)  # a marker extraction moved out of its paragraph


# MathJax writes \tag{} as an <mlabeledtr> with the tag first; browsers' MathML has no such row, so the equation
# falls apart. A plain row with the tag after the equation draws it as the page did.
LABELED = re.compile(r"<mlabeledtr([^>]*)>(<mtd[^>]*>.*?</mtd>)(.*?)</mlabeledtr>", re.S)


def restore_math(html: str, table: dict[str, str]) -> str:
    return re.sub(r"⟦[mic]\d+⟧", lambda m: LABELED.sub(r"<mtr\1>\3\2</mtr>", table.get(m.group(0), m.group(0))), html)
