"""End to end through extraction: what a real page holds must reach the numbered blocks."""
from magazine.capture import extract_page
from magazine.source import number_blocks

FILLER = "<p>" + "Words of the article, plain and many. " * 40 + "</p>"
PAGE = f"""<html><head><title>T</title></head><body><nav>menu</nav><article>
<h1 class="section-title">A heading</h1>{FILLER}
<p>Display math:</p><div class="MathJax_Display"><span class="MathJax"><nobr>v</nobr><span class="MJX_Assistive_MathML">
<math display="block"><mi>y</mi></math></span></span></div><script type="math/tex; mode=display">y</script>
<p>Inline <math alttext="x_i"><msub><mi>x</mi><mi>i</mi></msub></math> and add all links from <code>&lt;a&gt;</code> tags to the frontier.</p>
<img src="figs/diagram.svg" alt="a diagram">
<img src="data:image/gif;base64,R0" srcset="lazy-400.png 400w, lazy-1200.png 1200w" alt="lazy">
<p><img src="https://cdn.example.com/media/X?format=jpg" alt="cdn"></p>
<div class="thumbs"><a href="https://youtu.be/talk"><img src="thumb.png" alt="the talk"></a></div>
{FILLER}</article></body></html>"""


def test_extraction_keeps_math_code_images_and_headings():
    frag = extract_page(PAGE, "https://x.com/post/")
    html, n = number_blocks(frag)
    assert html.count("<math") == 2 and ">v<" not in html
    assert "<h1>A heading</h1>" in html.replace(' data-b="1"', "")
    assert any("links from <code>&lt;a&gt;</code> tags to the frontier" in b for b in html.split("\n"))
    for src in ("https://x.com/post/figs/diagram.svg", "https://x.com/post/lazy-1200.png",
                "https://cdn.example.com/media/X?format=jpg", "https://x.com/post/thumb.png"):
        assert f'src="{src}"' in html


def test_codeforces_statement_taken_whole():
    from magazine.capture import site_fragment
    page = ('<html><body><div id="sidebar">ads</div><div class="problem-statement"><div class="header">'
            '<div class="title">A. Accuracy-Preserving Summation</div>'
            '<div class="time-limit"><div class="property-title">time limit per test</div>10 seconds</div></div>'
            '<div><p>There is a sequence.</p><p>Each value can be one of the following:</p><ul><li>a number</li></ul></div>'
            '<div class="input-specification"><div class="section-title">Input</div><p>One line.</p></div>'
            '<div class="sample-tests"><div class="section-title">Examples</div><div class="sample-test">'
            '<div class="input"><div class="title">Input</div><pre>2 1 2</pre></div>'
            '<div class="output"><div class="title">Output</div><pre>{d:1,2}</pre></div></div></div></div></body></html>')
    frag = site_fragment(page, "https://codeforces.com/contest/1953/problem/A")
    assert "<h1>A. Accuracy-Preserving Summation</h1>" in frag and "<h2>Input</h2>" in frag and "<h3>Output</h3>" in frag
    assert "<li>a number</li>" in frag and "<pre>{d:1,2}</pre>" in frag and "time limit per test" in frag
    assert "<div" not in frag and "ads" not in frag
    assert site_fragment(page, "https://example.com/x") is None


def test_wikipedia_chrome_dropped_and_equations_not_bulleted():
    page = (f'<html><body><div class="mw-parser-output"><h2>Formal definition<span class="mw-editsection">'
            f'<span class="mw-editsection-bracket">[</span><a href="?action=edit">edit</a>'
            f'<span class="mw-editsection-bracket">]</span></span></h2>'
            f'<table class="sidebar"><tr><td>Complex analysis</td></tr></table>{FILLER}'
            f'<p>The integer is</p><dl><dd><math display="block"><mi>w</mi></math></dd></dl>{FILLER}</div></body></html>')
    html = extract_page(page, "https://en.wikipedia.org/wiki/Winding_number")
    assert "edit" not in html and "[" not in html and "Complex analysis" not in html
    assert "<li" not in html and "<math" in html



def test_display_math_between_paragraphs_is_its_own_block():
    # MathJax 3 sets a displayed formula between paragraphs, outside any <p>; as loose text extraction can drop it
    from magazine.source import protect_math
    page = ('<html><body><div><p>A simple example is the cubic polynomial:</p>'
            '<mjx-container class="MathJax" jax="CHTML" display="true"><mjx-math display="true" aria-hidden="true">'
            '<mjx-mi>p</mjx-mi></mjx-math><mjx-assistive-mml display="block"><math display="block"><mi>p</mi>'
            '</math></mjx-assistive-mml></mjx-container><p>To visualize this cubic, we plot it.</p></div></body></html>')
    html, table = protect_math(page)
    assert "<p>⟦m1⟧</p>" in html and "<math" in table["⟦m1⟧"]
