from types import SimpleNamespace

import pytest

from magazine.capture import (arxiv_atom_meta, arxiv_id, capture_html, finish, is_heading, pdf_paragraphs,
                              pick_subtitle, readme_base, vtt_to_paragraphs)


def test_arxiv_id():
    assert arxiv_id("https://arxiv.org/abs/2301.13142") == "2301.13142"
    assert arxiv_id("https://arxiv.org/pdf/2301.13142v2.pdf") == "2301.13142v2"


def test_pdf_paragraphs_joins_lines_and_hyphens():
    text = "Self-compressing net-\nworks shrink\nthemselves.\n\nSecond para.\n\x0c3\n"
    assert pdf_paragraphs(text) == ["Self-compressing networks shrink themselves.", "Second para."]


def test_pdf_paragraphs_splits_off_headings():
    text = "Introduction\nThe ongoing revolution in the\ncapabilities of models.\n\nwe show that the\nnetwork shrinks.\n"
    assert pdf_paragraphs(text) == ["Introduction", "The ongoing revolution in the capabilities of models.",
                                    "we show that the network shrinks."]


def test_pdf_heading_detection():
    assert is_heading("Introduction") and is_heading("3.1 Differentiable Quantization")
    assert not is_heading("Second para.") and not is_heading("james.imber@imgtec.com")
    assert not is_heading("word " * 12)
    assert not is_heading("𝐿 ∑ 𝑧𝑙 𝑁 𝑙=1") and not is_heading("𝟏𝑏𝑗 >0 ∑")  # equation pieces from PDF text


def test_arxiv_atom_meta():
    atom = ('<feed xmlns="http://www.w3.org/2005/Atom"><title>ArXiv Query</title><entry>'
            '<published>2023-01-30T18:22:28Z</published><title>Self-Compressing Neural\n  Networks</title>'
            '<author><name>Szabolcs Cséfalvay</name></author><author><name>James Imber</name></author></entry></feed>')
    assert arxiv_atom_meta(atom) == {"title": "Self-Compressing Neural Networks",
                                     "author": "Szabolcs Cséfalvay, James Imber", "date": "2023-01-30"}


def test_vtt_to_paragraphs_drops_timing_and_repeats():
    vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nhello there\n\n00:00:02.000 --> 00:00:03.000\nhello there\nhow are you\n"
    assert vtt_to_paragraphs(vtt) == ["hello there how are you"]


def test_readme_relative_images():
    base = readme_base("anthropics", "original_performance_takehome", "main")
    assert base == "https://github.com/anthropics/original_performance_takehome/raw/main/"
    # GitHub's rendered README writes images root-relative; plain relative paths must work too
    from urllib.parse import urljoin
    for src in ("/anthropics/original_performance_takehome/raw/main/a.png", "a.png"):
        assert urljoin(base, src) == "https://github.com/anthropics/original_performance_takehome/raw/main/a.png"


def test_capture_html_rejects_http_errors(tmp_path):
    # a 404 page (e.g. arXiv's "no HTML version") must not be captured as if it were the content
    shots = []
    page = SimpleNamespace(goto=lambda *a, **k: SimpleNamespace(status=404), url="https://x.org/missing",
                           screenshot=lambda **k: shots.append(k), close=lambda: None)
    with pytest.raises(RuntimeError, match="HTTP 404"):
        capture_html("https://x.org/missing", tmp_path, SimpleNamespace(new_page=lambda **k: page))
    assert shots == []


def test_pdf_keeps_digit_lines_inside_a_page():
    # only a page's first or last line can be a page number; table cells and years stay
    paras = pdf_paragraphs("Model Top-1\n\nResNet\n76\n\nOurs\n78\n\nEnd.\n3\n")
    assert "ResNet 76" in paras and "Ours 78" in paras and "3" not in paras


def test_pick_subtitle_prefers_the_spoken_language():
    assert pick_subtitle(["v.en.vtt", "v.es.vtt"], "es") == "v.es.vtt"  # not YouTube's translation into English
    assert pick_subtitle(["v.en.vtt", "v.es-orig.vtt"], None) == "v.es-orig.vtt"
    assert pick_subtitle(["v.en.vtt"], None) == "v.en.vtt"
    assert pick_subtitle([], "en") is None


def test_finish_does_not_call_a_short_readme_blocked(tmp_path):
    assert "status" not in finish(tmp_path, "<p>A tiny README.</p>", None, "t", check_blocked=False)
    assert finish(tmp_path, "", None, "t", check_blocked=False)["status"] == "unreadable"


def test_equation_runs_find_pdf_math_fragments():
    from magazine.capture import equation_runs
    paras = ["Plenty of ordinary prose words here in a sentence.", "(2)", "Where 𝛬0 is the original loss and the rest of it",
             "𝐿 1 ∑ 𝑧𝑙 𝑁 𝑙=1", "(3)", "More prose follows the equation here.", "james.imber@imgtec.com"]
    assert equation_runs(paras) == [(1, 1), (3, 4)]


def test_equation_box_covers_the_display_not_the_prose():
    from magazine.capture import equation_box
    lines = [("Where the vector is described in plain words here", 54, 100, 292, 110),
             ("𝑂", 120, 120, 130, 130), ("𝑧𝑙 = 𝐻𝑤 𝑊𝑤 ∑", 80, 132, 250, 142), ("(5)", 280, 132, 292, 142),
             ("Once a channel can be compressed to zero bits", 54, 160, 292, 170),
             ("𝑥 in the other column", 330, 132, 400, 142)]
    assert equation_box(lines, ["(5)"], page_width=612) == (80, 120, 292, 142)


def test_pdf_lines_decode_utf8_layout():
    from magazine.capture import pdf_lines_from
    xhtml = ('<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml"><body><doc>'
             '<page width="612.0" height="792.0"><flow><block><line xMin="1" yMin="2" xMax="3" yMax="4">'
             '<word xMin="1" yMin="2" xMax="3" yMax="4">𝑧𝑙</word><word xMin="1" yMin="2" xMax="3" yMax="4">∑</word>'
             '</line></block></flow></page></doc></body></html>').encode()
    assert pdf_lines_from(xhtml) == {1: (612.0, [("𝑧𝑙 ∑", 1.0, 2.0, 3.0, 4.0)])}


def test_equation_box_starts_from_its_own_number():
    # equations (4) and (5) share a piece; the run for (5) must crop (5)
    from magazine.capture import equation_box
    lines = [("𝑧𝑙 = 𝐼𝑙 𝐻𝑙 𝑊𝑙 ∑", 80, 100, 228, 112), ("𝑏𝑙𝑖", 232, 98, 250, 108), ("(4)", 280, 100, 292, 112),
             ("Where the sizes are defined in words here", 54, 130, 292, 140),
             ("𝑏𝑙𝑖", 120, 160, 140, 170), ("𝑧𝑙 = 𝐻𝑤 𝑊𝑤 ∑", 80, 172, 250, 182), ("(5)", 280, 172, 292, 182)]
    assert equation_box(lines, ["𝑏𝑙𝑖", "𝑧𝑙 = 𝐻𝑤 𝑊𝑤 ∑", "(5)"], page_width=612) == (80, 160, 292, 182)


def test_strip_math_tail_before_an_equation_image():
    from magazine.capture import strip_math_tail
    assert strip_math_tail("the optimisation objective: 𝛬(𝑥) = 𝛬0 (𝑥) + γ𝑄") == "the optimisation objective:"
    assert strip_math_tail("including this relationship: 𝐼") == "including this relationship:"
    assert strip_math_tail("as was shown in 2023") == "as was shown in 2023"


class _WalledPage:
    """A fake page that gets a human check, then renders whatever HTML it is given."""
    def __init__(self):
        self.html = "<html><head><title>Just a moment...</title></head><body>Verify you are human</body></html>"
        self.url = "https://codeforces.com/contest/1953/problem/A"
    def goto(self, *a, **k): return SimpleNamespace(status=403)
    def content(self): return self.html
    def title(self): return "Just a moment..."
    def set_content(self, html, **k): self.html = html
    def wait_for_load_state(self, *a, **k): pass
    def evaluate(self, js, *a): return {"palette": ["#ffffff"], "fonts": ["verdana"]} if "palette" in js else [] if "drawn" in js else None
    def screenshot(self, **k): pass
    def close(self): pass


def test_a_walled_page_is_read_through_the_users_safari(tmp_path, monkeypatch):
    import magazine.capture as capture_mod
    page = "<html><head><title>A. Accuracy-Preserving Summation</title></head><body><article><p>" + "word " * 200 + "</p></article></body></html>"
    seen = []
    monkeypatch.setattr(capture_mod, "read_in_safari", lambda url: seen.append(url) or page)
    meta = capture_html("https://codeforces.com/contest/1953/problem/A", tmp_path, SimpleNamespace(new_page=lambda **k: _WalledPage()))
    assert seen == ["https://codeforces.com/contest/1953/problem/A"]
    assert meta.get("status") != "unreadable" and meta["via"] == "safari" and meta["blocks"] >= 1


def test_a_walled_page_stays_unreadable_without_safari(tmp_path, monkeypatch):
    import magazine.capture as capture_mod
    monkeypatch.setattr(capture_mod, "read_in_safari", lambda url: None)
    meta = capture_html("https://codeforces.com/contest/1953/problem/A", tmp_path, SimpleNamespace(new_page=lambda **k: _WalledPage()))
    assert meta["status"] == "unreadable"


def test_raw_tex_pages_get_typeset():
    from magazine.capture import needs_typesetting
    assert needs_typesetting('<p>Let $$$x_i$$$ be the sum.</p>')  # Codeforces / Polygon statements
    assert not needs_typesetting('<p>$$$x$$$</p><mjx-container><mjx-assistive-mml><math></math></mjx-assistive-mml></mjx-container>')
    assert not needs_typesetting('<p>No math here, it costs $5.</p>')


def test_old_mathjax_loaders_are_dropped_before_typesetting():
    from magazine.capture import without_mathjax
    page = ('<head><script type="text/x-mathjax-config">MathJax.Hub.Config({});</script>'
            '<script type="text/javascript" async\n src="https://codeforces.com/mathjax.codeforces.org/MathJax.js?config=TeX">'
            '</script><script src="/js/app.js"></script></head><body>$$$x$$$</body>')
    out = without_mathjax(page)
    assert "x-mathjax-config" not in out and "MathJax.js" not in out and "/js/app.js" in out and "$$$x$$$" in out


def test_drawn_figures_become_pictures(tmp_path):
    # a figure drawn by script (SVG, canvas) has no <img>; it must reach the page as a picture of itself
    from magazine.capture import _LazyBrowser
    words = "<p>" + "Words of the post, plain and many. " * 60 + "</p>"
    post = tmp_path / "post.html"
    post.write_text(f'<html><head><title>Post</title></head><body><article><h1>Post</h1>{words}'
                    '<figure><svg width="400" height="200"><rect width="400" height="200" fill="#c33"/></svg>'
                    f'<figcaption>A red box.</figcaption></figure>{words}<iframe width="400" height="200" '
                    f'srcdoc="<body style=background:#36c></body>"></iframe>{words}</article></body></html>')
    item = tmp_path / "item"
    item.mkdir()
    browser = _LazyBrowser()
    try:
        capture_html(post.as_uri(), item, browser)
    finally:
        browser.close()
    assert "img/01.png" in (item / "source.html").read_text() and "img/02.png" in (item / "source.html").read_text()
    assert (item / "img" / "01.png").read_bytes().startswith(b"\x89PNG") and not (item / "drawn").exists()
