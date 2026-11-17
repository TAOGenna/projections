<p align="center">
  <img src="docs/readme/landing.jpg" alt="The Projections landing: a glass card with the name and three steps, and the sample issue floating closed on a teal ground drawn over with machine studies" width="100%">
</p>

<h1 align="center">Projections</h1>

<p align="center"><i>A magazine your agents make from what you save and bookmark.</i></p>

<p align="center"><sub>AN AGENT SKILL &nbsp;·&nbsp; <a href="#set-up">SET UP</a> &nbsp;·&nbsp; <a href="#nº-01">Nº 01</a> &nbsp;·&nbsp; <a href="#nº-00">Nº 00</a> &nbsp;·&nbsp; <a href="#credits">CREDITS</a></sub></p>

<br>

You save things to read: a paper, a post, a repository, a contest problem. Projections reads them for you, in full,
and binds them into an issue. Every piece keeps its own world, its colours, figures, structure, formulas and code,
inside one house frame. Each opens on a spread drawn from its own material, and the issue turns like paper in your
browser. Nothing is summarised and nothing is cut.

<br>

<table>
  <tr>
    <td width="33%" valign="top"><b>I &nbsp;·&nbsp; SAVE</b><br><sub>Paste links into <code>inbox.md</code> as you find them, one per line.</sub></td>
    <td width="33%" valign="top"><b>II &nbsp;·&nbsp; RUN</b><br><sub>Type <code>/issue</code> to your agent when you want an issue. Every link is captured whole and given an opener.</sub></td>
    <td width="33%" valign="top"><b>III &nbsp;·&nbsp; READ</b><br><sub>It opens in your browser, and <code>magazine open</code> brings it back where you left off. Spreads turn with ← →, ⌘+ ⌘− zoom, the contents takes you to a chapter, a typed page number and ⏎ takes you to that page. Every issue also comes as a PDF of single pages.</sub></td>
  </tr>
</table>

<br>

## Set up

You need macOS, [Homebrew](https://brew.sh) and an agent that runs skills: Projections ships as a
[Claude Code](https://claude.com/claude-code) skill in `.claude/skills/issue`.

```bash
git clone https://github.com/TAOGenna/projections
cd projections && brew install uv poppler yt-dlp
uv sync && uv run playwright install chromium
```

Then put links in `inbox.md`, open your agent in the folder, and type `/issue`. When it's done, the issue opens in
your browser. To come back to it any time, right where you left off:

```bash
uv run python -m magazine open            # the latest issue
uv run python -m magazine open 2026-11    # an earlier one
```

<br>

## Nº 01

<sub>NOVEMBER 2026 &nbsp;·&nbsp; SIX PIECES &nbsp;·&nbsp; 29 SPREADS</sub>

<p align="center">
  <img src="docs/readme/n01-winding-numbers.jpg" alt="Nº 01, chapter IV: Winding Numbers on Discrete Surfaces, its figures standing as objects on a slate ground" width="100%">
  <br><sub><i>IV · Winding Numbers on Discrete Surfaces</i> &nbsp;·&nbsp; the project page's own figures, as objects on a slate ground</sub>
</p>

<table>
  <tr>
    <td width="50%"><img src="docs/readme/n01-cover.jpg" alt="The front of Nº 01"><br><sub><i>The front</i> &nbsp;·&nbsp; the same drawing every issue, its number in the box</sub></td>
    <td width="50%"><img src="docs/readme/n01-contents.jpg" alt="The contents of Nº 01"><br><sub><i>Contents</i> &nbsp;·&nbsp; six pieces, one month</sub></td>
  </tr>
  <tr>
    <td><img src="docs/readme/n01-compilers.jpg" alt="Chapter I, Compilers for Machine Learning"><br><sub><i>I · Compilers for Machine Learning</i> &nbsp;·&nbsp; a course syllabus, lowered from graph to loops to GPU</sub></td>
    <td><img src="docs/readme/n01-self-compressing.jpg" alt="Chapter II, Self-Compressing Neural Networks"><br><sub><i>II · Self-Compressing Neural Networks</i> &nbsp;·&nbsp; a paper, its channels giving up their bits</sub></td>
  </tr>
  <tr>
    <td><img src="docs/readme/n01-take-home.jpg" alt="Chapter III, The Original Performance Take-Home"><br><sub><i>III · The Original Performance Take-Home</i> &nbsp;·&nbsp; a repository on GitHub's own dark canvas</sub></td>
    <td><img src="docs/readme/n01-crawler.jpg" alt="Chapter V, Crawling a Billion Web Pages"><br><sub><i>V · Crawling a Billion Web Pages</i> &nbsp;·&nbsp; a post, its twelve machines drawn as a system</sub></td>
  </tr>
  <tr>
    <td><img src="docs/readme/n01-codeforces.jpg" alt="Chapter VI, a Codeforces problem with a plain opener"><br><sub><i>VI · Accuracy-Preserving Summation</i> &nbsp;·&nbsp; a contest problem: a plain opener, so nothing hints at the solution</sub></td>
    <td><img src="docs/readme/n01-winding-text.jpg" alt="A text spread from chapter IV"><br><sub><i>Inside IV</i> &nbsp;·&nbsp; the page in full, its figures and its own type set in the house's</sub></td>
  </tr>
</table>

<br>

## Nº 00

<sub>A SAMPLE ISSUE &nbsp;·&nbsp; THREE PIECES &nbsp;·&nbsp; 29 SPREADS &nbsp;·&nbsp; MADE FOR THE SITE</sub>

<p align="center">
  <img src="docs/readme/n00-jpeg.jpg" alt="Nº 00, chapter I: JPEG Compression, the flamingos at falling quality and the sixty-four cosines" width="100%">
  <br><sub><i>I · JPEG Compression</i> &nbsp;·&nbsp; the essay's flamingos at falling JPEG quality, and the sixty-four cosines</sub>
</p>

<table>
  <tr>
    <td width="50%"><img src="docs/readme/n00-muon.jpg" alt="Chapter II, Deriving Muon"><br><sub><i>II · Deriving Muon</i> &nbsp;·&nbsp; the post's bubble chamber, and singular values pushed to one</sub></td>
    <td width="50%"><img src="docs/readme/n00-matmul.jpg" alt="Chapter III, Matrix Multiplication on RDNA3"><br><sub><i>III · Matrix Multiplication on RDNA3</i> &nbsp;·&nbsp; A × B = C as a cube, one tile rising through it</sub></td>
  </tr>
  <tr>
    <td><img src="docs/readme/n00-muon-text.jpg" alt="A text spread from Deriving Muon with typeset equations"><br><sub><i>Inside II</i> &nbsp;·&nbsp; on the author's green page, every formula typeset</sub></td>
    <td><img src="docs/readme/n00-matmul-text.jpg" alt="A text spread from the matrix multiplication post with code and diagrams"><br><sub><i>Inside III</i> &nbsp;·&nbsp; every listing and hand-drawn diagram of the post</sub></td>
  </tr>
  <tr>
    <td><img src="docs/readme/n00-jpeg-text.jpg" alt="A text spread from JPEG Compression"><br><sub><i>Inside I</i> &nbsp;·&nbsp; the essay's own pictures, in its order</sub></td>
    <td><img src="docs/readme/n00-cover.jpg" alt="The front of Nº 00"><br><sub><i>The front</i> &nbsp;·&nbsp; Nº 00, a sample issue</sub></td>
  </tr>
</table>

<p align="center">
  <img src="docs/readme/landing-open.jpg" alt="The landing with the sample issue open on chapter I" width="100%">
  <br><sub>On the site, Nº 00 floats closed on its cover; it opens and turns right there, page by page</sub>
</p>

<br>

## How an issue is made

`/issue` follows the house's guidelines in [`policies.md`](policies.md), with the `magazine` package doing the
mechanical parts:

1. **Capture.** `uv run python -m magazine start` reads every link in `inbox.md` into `issues/<month>/items/`: the
   page's own text and structure, its images, its formulas as MathML (typeset where a page only had TeX, cropped as
   set from a PDF), its code, and its colours. Figures a page draws with script are kept as pictures of themselves.
   A page that wants a human check is read through your own Safari, where you pass it yourself.
2. **Compose.** The agent writes each chapter: an opener made from the piece's own material, and the piece in full
   across as many spreads as it needs, in its own colours and the house type.
3. **Assemble, bake, check.** `assemble` binds the chapters into `index.html`, `bake` turns heavy drawings into
   images so the issue turns fast, and `check` fails on any overflow, hidden block, broken image or faked type.
4. **Open.** `open` opens the issue in your browser; the reader remembers the spread you stopped at, per issue. Click a row of the contents to go to its chapter, type a page number and press ⏎ to go to that page, and click the masthead at the top left of any page to go back to the contents (Back returns you), and press Home (fn ← on a Mac) to go to the front. `#s55` in the address is spread 55, `#p108` page 108.
5. **Archive.** `archive` clears the inbox for next time.

Your issues stay on your machine: `issues/` is not tracked.

<table>
  <tr><td><code>magazine/</code></td><td><sub>capture, assembly, bake, check, and the reader with its page turn</sub></td></tr>
  <tr><td><code>.claude/skills/issue/</code></td><td><sub>the <code>/issue</code> skill</sub></td></tr>
  <tr><td><code>policies.md</code></td><td><sub>the house style: the frame, the type, openers as invitations, grounds and tones</sub></td></tr>
  <tr><td><code>site/</code></td><td><sub>the landing and Nº 00; <code>site/making/</code> holds the scripts that made them</sub></td></tr>
  <tr><td><code>tests/</code></td><td><sub><code>uv run pytest</code></sub></td></tr>
</table>

## Later

What it does today is the core: every piece in full, rendered in the browser, turning like paper. What would come
next:

- [ ] **Ask about what you're reading.** Select a passage in an issue and copy it, and the copy carries where it came
  from: the issue, the chapter, the piece's captured source and the exact block. Pasted into Claude Code or Claude
  desktop, your agent knows what you're pointing at and can open the piece around it, since everything is local.
  Reading a post or a paper, you always have questions.
- [ ] **A print edition.** Issues already print from the browser; a proper edition would add bleeds, crop marks and
  a PDF laid out as spreads.
- [ ] **Phones.** The landing and the reader scale down whole; narrow screens deserve a layout of their own.
- [ ] **Your notes kept with the issue.** Highlights and margin notes saved beside the issue, on your machine.
- [ ] **An archive.** Every past issue in one place, searchable across all of them.

## Credits

The look follows Taili Zhuang's 2020 architecture portfolio: its hairline box, its Garamond capitals over light Open
Sans, its openers that show the work rather than explain it. The front of every issue is a drawing from that
portfolio.

**Nº 00:** *JPEG compression*, [Sophie Wang](https://www.sophielwang.com/blog/jpeg) · *Deriving Muon*,
[Jeremy Bernstein](https://jeremybernste.in/writing/deriving-muon) · *Optimizing Matrix Multiplication on RDNA3*,
[Seb-V](https://seb-v.github.io/optimization/update/2025/01/20/Fast-GPU-Matrix-multiplication.html).

**Nº 01:** *Compilers for Machine Learning*, [10-411, Carnegie Mellon](https://10-411.com) · *Self-Compressing
Neural Networks*, [Szabolcs Cséfalvay and James Imber](https://arxiv.org/abs/2301.13142) · *The Original Performance
Take-Home*, [Anthropic](https://github.com/anthropics/original_performance_takehome) · *Winding Numbers on Discrete
Surfaces*, [Nicole Feng, Mark Gillespie and Keenan Crane](https://nzfeng.github.io/research/WNoDS/index.html) ·
*Crawling a Billion Web Pages*, [Andrew Chan](https://andrewkchan.dev) · *Accuracy-Preserving Summation*,
[Codeforces 1953A](https://codeforces.com/contest/1953/problem/A).

Every piece's words and pictures are its authors'. The openers' drawings are Projections' own.
