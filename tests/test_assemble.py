import pytest

from magazine.assemble import assemble, expand_sources


def test_expand_range_and_single(tmp_path):
    item = tmp_path / "items" / "p"; item.mkdir(parents=True)
    (item / "source.html").write_text('<p data-b="1">a</p><p data-b="2">b</p><p data-b="3">c</p>')
    out = expand_sources('<div><x-src item="p" from="2" to="3"></x-src><x-src item="p" b="1"></x-src></div>', tmp_path / "items")
    assert out == '<div><p data-b="2" data-src="p">b</p><p data-b="3" data-src="p">c</p><p data-b="1" data-src="p">a</p></div>'


def test_expand_rejects_bad_range(tmp_path):
    (tmp_path / "items" / "p").mkdir(parents=True)
    (tmp_path / "items" / "p" / "source.html").write_text('<p data-b="1">a</p>')
    with pytest.raises(ValueError, match="p.*5"):
        expand_sources('<x-src item="p" from="1" to="5"></x-src>', tmp_path / "items")


def test_assemble_writes_index(tmp_path):
    (tmp_path / "issue.json").write_text('{"number": 1, "month": "2026-12"}')
    (tmp_path / "items").mkdir(); (tmp_path / "chapters").mkdir()
    (tmp_path / "chapters" / "00-cover.html").write_text('<section class="spread" data-item="_cover">Hi</section>')
    html = assemble(tmp_path).read_text()
    assert "<title>Issue 1 · December 2026</title>" in html and 'href="style.css"' in html
    assert (tmp_path / "reader.js").exists() and (tmp_path / "reader.css").exists()


def test_paginate_numbers_pages_by_spread_and_resolves_chapter_pages():
    from magazine.assemble import paginate
    body = ('<section class="spread" data-item="_cover"></section>'
            '<section class="spread" data-item="_contents"><a href="#p{{page:b}}">p. {{page:b}}</a>'
            '<div class="folio l">99</div><div class="folio r">99</div></section>'
            '<section class="spread gutter" data-item="a"></section>'
            '<section class="spread" data-item="b"><div class="folio l"></div><div class="folio r x">7</div></section>')
    out = paginate(body)
    assert '<a href="#p6">p. 6</a>' in out
    assert '<div class="folio l">2</div><div class="folio r">3</div>' in out
    assert '<div class="folio l">6</div><div class="folio r x">7</div>' in out
    with pytest.raises(ValueError, match="nope"):
        paginate('<section class="spread" data-item="a">{{page:nope}}</section>')
