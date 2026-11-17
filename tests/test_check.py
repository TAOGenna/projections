import json

from magazine.check import placement_problems, render_problems


def _item(items, slug, n, status="ok"):
    d = items / slug; d.mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({"slug": slug, "status": status, "blocks": n}))


def test_placement_reports_missing_duplicates_and_absent(tmp_path):
    _item(tmp_path, "p", 4); _item(tmp_path, "dead", 0, "unreadable")
    html = '<section class="spread" data-item="p"><p data-src="p" data-b="1"></p>' \
           '<p data-src="p" data-b="1"></p><p data-src="p" data-b="4"></p></section>'
    assert placement_problems(html, tmp_path) == [
        "p: blocks 2–3 missing", "p: block 1 placed 2 times", "dead: no spread"]


def test_render_flags_overflow_and_broken_image(tmp_path):
    (tmp_path / "reader.css").write_text(".spread{width:1600px;height:1000px;position:relative;overflow:hidden}")
    page = tmp_path / "index.html"
    page.write_text('<link rel="stylesheet" href="reader.css">'
        '<section class="spread" data-item="a"><div style="height:1300px"></div></section>'
        '<section class="spread" data-item="b"><img src="nope.png"></section>')
    probs = render_problems(page)
    assert any(p.startswith("spread 1 (a): overflows") for p in probs)
    assert any("spread 2 (b)" in p and "image" in p for p in probs)


def test_render_flags_text_cut_by_columns_but_not_clipped_bleed(tmp_path):
    # text spilling out of a two-column box is lost; an image bleeding inside an overflow:hidden box is design
    (tmp_path / "reader.css").write_text(".spread{width:1600px;height:1000px;position:relative;overflow:hidden}")
    page = tmp_path / "index.html"
    words = "word " * 4000
    page.write_text('<link rel="stylesheet" href="reader.css">'
        f'<section class="spread" data-item="a"><div style="columns:2;width:700px;height:900px"><p>{words}</p></div></section>'
        '<section class="spread" data-item="b"><div style="position:absolute;inset:0;overflow:hidden">'
        '<div style="position:absolute;left:-200px;top:-100px;width:2400px;height:1400px;background:#ccc"></div></div></section>')
    probs = render_problems(page)
    assert any(p.startswith("spread 1 (a): overflows") for p in probs)
    assert not any("spread 2" in p for p in probs)


def test_placement_counts_only_blocks_on_spreads_and_catches_altered_text(tmp_path):
    _item(tmp_path, "p", 2)
    (tmp_path / "p" / "source.html").write_text('<p data-b="1">the words</p>\n<p data-b="2">more words</p>')
    html = '<section class="spread" data-item="p"><p data-src="p" data-b="1">the wordz</p></section>' \
           '<p data-src="p" data-b="2">more words</p>'
    assert placement_problems(html, tmp_path) == ["p: block 2 missing", "p: block 1 altered"]


def test_render_flags_hidden_and_self_clipped_text_but_not_known_missing_images(tmp_path):
    (tmp_path / "reader.css").write_text(".spread{width:1600px;height:1000px;position:relative;overflow:hidden}")
    page = tmp_path / "index.html"
    lines = "\n".join(f"line {i}" for i in range(80))
    page.write_text('<link rel="stylesheet" href="reader.css">'
        '<section class="spread" data-item="a"><p data-src="a" data-b="1" style="display:none">hidden words</p></section>'
        f'<section class="spread" data-item="b"><pre style="overflow:auto;height:60px">{lines}</pre></section>'
        '<section class="spread" data-item="c"><img src="https://invalid.example/x.png" data-missing="1"></section>')
    probs = render_problems(page)
    assert any(p.startswith("spread 1 (a)") and "hidden" in p for p in probs)
    assert any(p.startswith("spread 2 (b): overflows") for p in probs)
    assert not any("spread 3" in p for p in probs)


def test_render_flags_faked_bold_and_italic(tmp_path):
    # a weight or style the page never loads gets faked by the browser, and looks like another typeface
    page = tmp_path / "index.html"
    page.write_text('<style>@font-face{font-family:"T";src:local("Helvetica");font-weight:300}'
        '.spread{width:1600px;height:1000px;position:relative;overflow:hidden}</style>'
        '<section class="spread" data-item="a"><p style="font-family:T;font-weight:300">fine</p>'
        '<p style="font-family:T;font-weight:600">bold</p>'
        '<p style="font-family:T;font-weight:300;font-style:italic">slanted</p></section>')
    probs = render_problems(page)
    assert any(p.startswith("spread 1 (a)") and "T 600 normal" in p for p in probs)
    assert any("T 300 italic" in p for p in probs)
    assert not any("T 300 normal" in p for p in probs)


def test_render_ignores_decorative_layers(tmp_path):
    # faint giant type behind a chapter bleeds on purpose; it is marked aria-hidden and isn't content
    (tmp_path / "reader.css").write_text(".spread{width:1600px;height:1000px;position:relative;overflow:hidden}")
    page = tmp_path / "index.html"
    page.write_text('<link rel="stylesheet" href="reader.css">'
        '<section class="spread" data-item="a"><div aria-hidden="true" style="position:absolute;inset:0;overflow:hidden">'
        '<div style="position:absolute;left:-300px;top:20px;font-size:180px;white-space:nowrap">UOPS · REWRITES · LOADS · STORES</div>'
        '</div></section>')
    assert render_problems(page) == []


def test_render_flags_content_across_or_against_the_gutter_but_not_decoration(tmp_path):
    # the PDF cuts each spread at 800px: text or a figure across it is cut; decoration may cross
    (tmp_path / "reader.css").write_text(".spread{width:1600px;height:1000px;position:relative;overflow:hidden}"
                                         " .spread *{position:absolute;top:100px;margin:0}")
    page = tmp_path / "index.html"
    page.write_text('<link rel="stylesheet" href="reader.css">'
        '<section class="spread" data-item="a"><p data-b="3" style="left:700px;width:300px">across the gutter</p></section>'
        '<section class="spread" data-item="b"><svg style="left:600px" width="400" height="100"></svg></section>'
        '<section class="spread" data-item="c"><p style="left:760px">x</p></section>'
        '<section class="spread" data-item="d"><svg aria-hidden="true" style="left:0" width="1600" height="900"></svg>'
        '<p style="left:60px;width:680px">left page</p><p style="left:860px;width:680px">right page</p></section>')
    probs = render_problems(page)
    assert "spread 1 (a): crosses the gutter, cut in two in the PDF: block 3" in probs
    assert any(p.startswith("spread 2 (b): crosses the gutter") and "svg" in p for p in probs)
    assert any(p.startswith("spread 3 (c): text within 60px of the gutter") for p in probs)
    assert not any("spread 4" in p for p in probs)


def test_render_lets_a_table_run_on_from_one_page_to_the_next(tmp_path):
    # a column a page, the gutter between them: a long table breaks at the foot of the left page, crossing nothing
    (tmp_path / "reader.css").write_text(".spread{width:1600px;height:1000px;position:relative;overflow:hidden}")
    page = tmp_path / "index.html"
    rows = "".join(f"<tr><td>{n}</td></tr>" for n in range(80))
    page.write_text('<link rel="stylesheet" href="reader.css"><section class="spread" data-item="a">'
        '<div style="position:absolute;left:60px;top:80px;width:1480px;height:840px;columns:2;column-gap:120px;column-fill:auto">'
        f'<table style="width:100%">{rows}</table></div></section>')
    assert not any("gutter" in p for p in render_problems(page))
