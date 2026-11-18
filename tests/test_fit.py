from magazine.fit import fit


def test_fit_fills_each_box_then_moves_on(tmp_path):
    item = tmp_path / "items" / "p"; item.mkdir(parents=True)
    tall = "<p data-b='{}' style='height:300px;margin:0'>x</p>"
    (item / "source.html").write_text("".join(tall.format(n) for n in range(1, 6)) + "<p data-b='6' style='height:900px;margin:0'>big</p>")
    (tmp_path / "index.html").write_text(
        "<style>.box{position:absolute;width:300px;height:640px;overflow:hidden}</style><main class='deck'></main>")
    # two 300px blocks fill a 640px box; a block bigger than the box still takes one, so the fit moves on
    assert fit(tmp_path, "p", 1, 6, "box") == [(1, 2), (3, 4), (5, 5), (6, 6)]
