from magazine.source import (localize_images, number_blocks, protect_code, protect_headings, protect_images,
                             protect_math, restore_headings, restore_math)


def test_number_blocks():
    html, n = number_blocks("loose<h2>T</h2><p>a</p><p> </p><pre>x</pre>")
    assert n == 4
    assert '<p data-b="1">loose</p>' in html and '<pre data-b="4">x</pre>' in html


def test_localize_picks_real_image(tmp_path):
    seen = []
    frag = '<p><img src="data:image/gif;base64,R0" data-src="/big.jpg"></p>' \
           '<p><img srcset="/s.png 400w, /l.png 1200w"></p>'
    out = localize_images(frag, "https://x.com/a/", tmp_path, "items/s/img/",
                          fetch=lambda u: seen.append(u) or b"img")
    assert seen == ["https://x.com/big.jpg", "https://x.com/l.png"]
    assert 'src="items/s/img/01.jpg"' in out and "srcset" not in out


def test_localize_keeps_remote_on_failure(tmp_path):
    def boom(u): raise OSError
    out = localize_images('<img src="https://x.com/a.png">', "https://x.com", tmp_path, "p/", fetch=boom)
    assert 'src="https://x.com/a.png"' in out and "data-missing" in out


def test_math_survives_extraction():
    page = '<p>Sum <span class="MathJax"><span>x i</span></span>' \
           '<span class="MJX_Assistive_MathML"><math><mi>x</mi></math></span> ok</p>'
    protected, table = protect_math(page)
    assert "<math" not in protected and "x i" not in protected
    assert restore_math(protected, table).count("<math>") == 1


def test_katex_math_survives_extraction():
    page = '<p>Sum <span class="katex"><span class="katex-mathml"><math><semantics><mi>x</mi>' \
           '<annotation encoding="application/x-tex">x</annotation></semantics></math></span>' \
           '<span class="katex-html" aria-hidden="true">x i</span></span> ok</p>'
    protected, table = protect_math(page)
    assert "<math" not in protected and "x i" not in protected
    assert restore_math(protected, table).count("<math>") == 1



def test_headings_survive_extraction():
    # some layouts make extraction drop real section headings; a text marker carries them through
    prot = protect_headings('<div><h1 class="section-title">What <i>problem</i>?</h1><p>text</p></div>')
    assert "<h1" not in prot and "⟦h1⟧What <i>problem</i>?" in prot
    assert restore_headings('<p>⟦h1⟧What <i>problem</i>?</p><p>text</p>') == '<h1>What <i>problem</i>?</h1><p>text</p>'


def test_restore_headings_drops_stray_markers():
    assert restore_headings("<li>⟦h3⟧x</li>") == "<li>x</li>"


def test_mathjax2_display_math_kept_once():
    page = ('<p>Before.</p><div class="MathJax_Display"><span class="MathJax"><nobr>v</nobr>'
            '<span class="MJX_Assistive_MathML MJX_Assistive_MathML_Block"><math display="block"><mi>x</mi></math>'
            '</span></span></div><script type="math/tex; mode=display">x</script><p>After.</p>')
    protected, table = protect_math(page)
    out = restore_math(protected, table)
    assert out.count("<math") == 1 and ">v<" not in out


def test_commonhtml_math_not_doubled():
    page = ('<p>Let <span class="mjx-chtml MathJax_CHTML"><span class="mjx-char">xi</span>'
            '<span class="MJX_Assistive_MathML"><math><mi>x</mi></math></span></span> be.</p>')
    protected, table = protect_math(page)
    assert "xi" not in protected and restore_math(protected, table).count("<math") == 1


def test_math_without_assistive_mathml_keeps_tex():
    page = '<p>Let <span class="MathJax"><nobr>xi</nobr></span><script type="math/tex">x_i</script> be.</p>'
    protected, table = protect_math(page)
    out = restore_math(protected, table)
    assert "xi" not in protected and "x_i" in out


def test_bare_mathml_is_protected():
    # LaTeXML (arXiv's HTML papers) writes plain <math>; extraction would turn it into TeX text
    protected, table = protect_math('<p>Sum <math alttext="x_i"><msub><mi>x</mi><mi>i</mi></msub></math> ok</p>')
    assert "<math" not in protected and restore_math(protected, table).count("<math") == 1


def test_protect_images_resolves_the_real_source():
    page = ('<div><p>a</p><img src="data:image/gif;base64,R0" srcset="/s.png 400w, /l.png 1200w">'
            '<p>b <img src="/badge"> c</p><svg viewBox="0 0 1 1"><rect/></svg></div>')
    protected, table = protect_images(page, "https://x.com/post/")
    assert '<img src="https://x.com/l.png"' in protected  # a named .png: extraction keeps it by itself
    assert "/badge" not in protected and "<svg" not in protected  # these travel as tokens
    out = restore_math(protected, table)
    assert 'src="https://x.com/badge"' in out and "<svg" in out


def test_protect_code_keeps_inline_code():
    protected, table = protect_code("<p>add all links from <code>&lt;a&gt;</code> tags</p><pre><code>x</code></pre>")
    assert protected.count("<code>") == 1  # the block's code stays as it is
    assert "<code>&lt;a&gt;</code>" in restore_math(protected, table)


def test_localize_names_files_by_their_bytes(tmp_path):
    svg = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>'
    out = localize_images('<img src="https://x.com/badge"><img src="https://x.com/pic">', "https://x.com",
                          tmp_path, "p/", fetch=lambda u: svg if u.endswith("badge") else b"\x89PNG\r\n")
    assert 'src="p/01.svg"' in out and 'src="p/02.png"' in out


def test_images_are_kept_no_bigger_than_ever_shown(tmp_path):
    # a 13,000 px figure costs a frozen frame to decode; 2,400 px covers every use at 2x
    from io import BytesIO
    from PIL import Image
    from magazine.source import shrink
    big = BytesIO(); Image.new("RGBA", (6000, 1500), (0, 0, 0, 0)).save(big, "PNG")
    p = tmp_path / "f.png"; p.write_bytes(big.getvalue())
    shrink(p)
    im = Image.open(p)
    assert im.size == (2400, 600) and im.mode == "RGBA"
    small = tmp_path / "s.png"; Image.new("RGB", (800, 600)).save(small)
    before = small.read_bytes(); shrink(small)
    assert small.read_bytes() == before  # already small: untouched


def test_wikipedia_math_keeps_its_mathml_not_its_picture():
    page = ('<p>The number <span class="mwe-math-element"><span class="mwe-math-mathml-inline mwe-math-mathml-a11y" '
            'style="display: none;"><math><mi>n</mi></math></span><img src="https://wikimedia.org/api/rest_v1/media/'
            'math/render/svg/abc" class="mwe-math-fallback-image-inline" aria-hidden="true" alt="{\\displaystyle n}">'
            '</span> winds.</p>')
    protected, table = protect_math(page)
    assert "<img" not in protected and "display: none" not in protected and "<math" not in protected
    out = restore_math(protected, table)
    assert out.count("<math") == 1 and "<img" not in out and "winds" in out


def test_hidden_mathml_is_lifted_out_of_its_hidden_wrapper():
    # Wikipedia now: MathML hidden in a span, MathJax's SVG beside it
    page = ('<p>Sum <span style="display: none;"><math class="mwe-math-element"><mi>n</mi></math></span>'
            '<mjx-container class="MathJax" jax="SVG"><svg><path d="M0"/></svg></mjx-container> ok</p>')
    protected, table = protect_math(page)
    assert "display: none" not in protected and "<svg" not in protected
    assert restore_math(protected, table).count("<math") == 1


def test_tagged_equation_keeps_its_tag_on_the_right():
    # MathJax writes \tag{⋆} as <mlabeledtr>, which browsers' MathML doesn't draw: the equation falls apart
    tagged = ('<math display="block"><mtable><mlabeledtr><mtd><mtext>(⋆)</mtext></mtd><mtd><mi>x</mi><mo>≤</mo>'
              '<mn>1</mn></mtd></mlabeledtr></mtable></math>')
    out = restore_math("<p>⟦m1⟧</p>", {"⟦m1⟧": tagged})
    assert "mlabeledtr" not in out
    assert "<mtr><mtd><mi>x</mi><mo>≤</mo><mn>1</mn></mtd><mtd><mtext>(⋆)</mtext></mtd></mtr>" in out
