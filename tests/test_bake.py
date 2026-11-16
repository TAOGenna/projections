from magazine.bake import bake

SPREAD = '<section class="spread" data-item="a" style="width:1600px;height:1000px;position:relative">{}</section>'
HEAVY = ('<svg class="layer" aria-hidden="true" width="1600" height="1000" style="position:absolute;left:0;top:0">'
         + "".join(f'<circle cx="{i}" cy="500" r="1"/>' for i in range(400)) + '</svg>')
LIGHT = '<svg class="layer" aria-hidden="true" width="1600" height="1000"><circle cx="5" cy="5" r="3"/></svg>'


def test_bake_turns_heavy_decoration_into_an_image(tmp_path):
    (tmp_path / "index.html").write_text(f'<html><body><main class="deck">{SPREAD.format(HEAVY + LIGHT)}</main></body></html>')
    assert bake(tmp_path) == 1
    html = (tmp_path / "index.html").read_text()
    assert html.count("<circle") == 1 and 'src="art/a-1.webp"' in html  # the light one stays vector
    assert (tmp_path / "art" / "a-1.webp").stat().st_size > 0
    assert bake(tmp_path) == 0  # nothing left to bake
