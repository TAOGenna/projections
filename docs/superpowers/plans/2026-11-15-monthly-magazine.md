# Monthly Magazine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `/issue` Claude Code skill and a small Python toolkit that turn a month of links in `inbox.md` into a magazine issue, laid out by Claude, where every item appears in full inside one house frame while keeping its own world.

**Architecture:** Approach A: Claude designs and writes every spread, every month. Code only covers what Claude must not do by hand:
- capturing each link faithfully to disk;
- pouring captured source text into the page verbatim, through an `<x-src>` tag, so it is never retyped;
- turning spreads with the keyboard and printing;
- checking that no source text is missing and no spread overflows.

The house frame lives in `policies.md` and in each issue's Claude-written `style.css`, never in templates.

**Tech Stack:** Python 3.11 managed with `uv`. Dependencies: `trafilatura>=2.0` (article extraction; brings `lxml`), `playwright` (rendering, screenshots, page styles), `pytest` (dev). System tools already installed: poppler (`pdftotext`, `pdfimages`, `pdftoppm`) and `yt-dlp`.

**Spec:** `docs/superpowers/specs/2026-11-15-monthly-magazine-design.md`

## Global Constraints

- Claude Code only. It runs locally, with no server, hosted service, accounts or sign-ins. It never gets around a paywall or login.
- Every item appears **in full**. The source's words reach the page only through `<x-src>` expansion, never retyped by Claude. Claude's own words always sit inside an element with class `editor`.
- Inbox: `inbox.md` at the repo root. Issues: `issues/YYYY-MM/`, each holding `index.html`, `style.css`, `reader.css`, `reader.js`, `issue.json`, `inbox.md` (the record), `chapters/`, `items/<slug>/` and `proofs/`.
- A captured item lives in `items/<slug>/` as `meta.json`, `source.html`, `screenshot.png` and `img/`.
- Spread design size: **1600 × 1000 CSS px** (16:10), one spread per screen. Print: `@page { size: 16in 10in; margin: 0 }`, one spread per page.
- The old experiments stay untouched and uncommitted: `fetch_bookmarks.py`, `test_fetch_bookmarks.py`, `issue/`, `proofs/`, `OFFPRINT.md`, `__pycache__/`.
- No other dependencies beyond those listed in Tech Stack.
- The front drawing `assets/front.jpg` is Taili Zhuang's work. It is never committed: `.gitignore` lists `front.jpg`.

## Review Focus

1. **Bot walls and JS-only pages** (Cloudflare "Just a moment…", empty shells): expect them marked `unreadable` with a reason, never captured as if the challenge page were the content. *Test: Task 3 `test_looks_blocked`.*
2. **Math in sources** (Codeforces MathJax formulas): expect each formula to appear once and readable as native MathML, not doubled ("𝑥 𝑖 𝑥 𝑖") or dropped by extraction. *Test: Task 2 `test_math_survives_extraction`.*
3. **Messy inbox lines** (same URL twice, `<url>`, trailing `.` or `)`, notes after `—`, `--` or ` - `): expect each URL captured once, with its note kept. *Test: Task 1 `test_parse_messy_lines`.*
4. **Lazy-loaded and relative images** (`data-src`, `srcset`, README images with relative paths): expect the real image downloaded, not a placeholder or a broken link. *Tests: Task 2 `test_localize_picks_real_image` and Task 4 `test_readme_relative_images`.*
5. **Re-running mid-month or after editing chapters** (`start` again, links added while the issue was being made): expect Claude's chapters kept, already-captured items skipped, and lines added mid-run left in the inbox. *Tests: Task 3 `test_capture_all_skips_existing` and Task 1 `test_archive_keeps_new_lines`.*

---

### Task 1: Repo setup and the inbox

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `inbox.md`, `magazine/__init__.py`, `magazine/inbox.py`, `magazine/__main__.py`
- Copy: `mockups/img/front.jpg` → `assets/front.jpg` (not committed)
- Test: `tests/test_inbox.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) Entry(url: str, note: str = "")`
  - `parse_inbox(text: str) -> list[Entry]`
  - `slug_for(url: str, taken: set[str]) -> str`
  - `archive(inbox: Path, issue_dir: Path, used: list[Entry]) -> None`
  - `magazine/__main__.py` with an argparse CLI and subcommands `start`, `assemble`, `check`, `archive`. This task implements only `archive`; later tasks fill in the others.

- [ ] **Step 1: Set up the repo**

Run `git init`. Write `pyproject.toml` (project `magazine`, `requires-python = ">=3.11"`, dependencies `trafilatura>=2.0` and `playwright`, dev group with `pytest`). Write `.gitignore` covering `.venv/`, `__pycache__/`, `data/` and `front.jpg`. Copy `mockups/img/front.jpg` to `assets/front.jpg`. It was made once from page 1 of `~/Downloads/Taili-Zhuang-Portfolio-2020.pdf` (5100 × 3300 px, his name painted white over (3330, 1530)–(4315, 1725), then resized to 3200 px wide). Write `inbox.md` containing the comment line `<!-- One link per line. Optional note after " — ". -->` and nothing else. Run `uv sync` and `uv run playwright install chromium`.
Expected: `uv run python -c "import trafilatura, playwright"` exits 0.

- [ ] **Step 2: Write the failing tests** in `tests/test_inbox.py`

```python
def test_parse_messy_lines():
    text = """<!-- comment -->
# heading
- https://a.com/x — first note
* <https://b.com/y>.
https://c.com/z -- second
- https://a.com/x - duplicate
- not a link
* [deeper understanding of winding numbers](https://d.io/wn/index.html)
* [ ] [crawling a billion pages](https://e.dev/)
- [x] https://f.com/done
"""
    assert parse_inbox(text) == [
        Entry("https://a.com/x", "first note"),
        Entry("https://b.com/y"),
        Entry("https://c.com/z", "second"),
        Entry("https://d.io/wn/index.html", "deeper understanding of winding numbers"),
        Entry("https://e.dev/", "crawling a billion pages"),
        Entry("https://f.com/done"),
    ]

def test_slug_for_is_readable_and_unique():
    taken = set()
    a = slug_for("https://codeforces.com/contest/1953/problem/A", taken); taken.add(a)
    b = slug_for("https://codeforces.com/contest/1953/problem/A?x=1", taken)
    assert a == "codeforces-1953-problem-a" and b == "codeforces-1953-problem-a-2"

def test_archive_keeps_new_lines(tmp_path):
    inbox = tmp_path / "inbox.md"
    inbox.write_text("<!-- c -->\n- https://a.com — n\n- https://new.com\n")
    archive(inbox, tmp_path / "issue", [Entry("https://a.com", "n")])
    assert inbox.read_text() == "<!-- c -->\n- https://new.com\n"
    assert "https://a.com — n" in (tmp_path / "issue" / "inbox.md").read_text()
```

- [ ] **Step 3: Run them to verify they fail**

Run: `uv run pytest tests/test_inbox.py -v`
Expected: FAIL with an ImportError.

- [ ] **Step 4: Implement `parse_inbox`, `slug_for`, `archive` in `magazine/inbox.py`**

- **`parse_inbox`:**
  - A line is an entry if, after stripping an optional `-` or `*` bullet and an optional `[ ]` or `[x]` checkbox, it starts with `http(s)://`, `<http`, or a markdown link `[text](url)`. For a markdown link, the URL comes from the parentheses and the link text becomes the note.
  - Strip `<>` and trailing `.,;)` from the URL.
  - The note is whatever follows the first ` — `, ` -- ` or ` - `.
  - Keep only the first occurrence of each URL.
- **`slug_for`:**
  - Build it from the domain without `www.` and its TLD, followed by the last 3 path parts.
  - Lowercase it, collapse every run of `[^a-z0-9]` into `-`, and cap it at 48 characters.
  - If the slug is already taken, add `-2`, `-3` and so on.
- **`archive`:**
  - Append the used entries to `issue_dir/inbox.md` as `- url — note` lines, creating the folder if needed.
  - Rewrite the inbox without the used entries' lines.

Also wire `python -m magazine archive [month]`. It reads the used entries from `issues/<month>/items/*/meta.json` (`url`, `note`), and `month` defaults to the latest `issues/*` folder.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_inbox.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock .gitignore inbox.md magazine tests
git commit -m "feat: inbox parsing, slugs and archiving"
```

---

### Task 2: Source blocks, images and math

**Files:**
- Create: `magazine/source.py`
- Test: `tests/test_source.py`

**Interfaces:**
- Produces:
  - `number_blocks(fragment_html: str) -> tuple[str, int]`. Every top-level block element gets `data-b="1".."n"`. Loose top-level text is wrapped in `<p>`. Empty blocks are dropped.
  - `localize_images(fragment_html: str, base_url: str, img_dir: Path, rel_prefix: str, fetch: Callable[[str], bytes] = download) -> str`
  - `download(url: str) -> bytes`, using urllib with a browser User-Agent and a 30 s timeout.
  - `protect_math(page_html: str) -> tuple[str, dict[str, str]]` and `restore_math(html: str, table: dict[str, str]) -> str`

- [ ] **Step 1: Write the failing tests** in `tests/test_source.py`

```python
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
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_source.py -v`
Expected: FAIL with an ImportError.

- [ ] **Step 3: Implement `magazine/source.py`**

- Parse with `lxml.html.fragments_fromstring`.
- **`localize_images`:**
  - Choose the image URL in this order: the largest `srcset` candidate, then `data-src` or `data-original`, then `src`. Skip `data:` URIs.
  - Resolve it against `base_url` with `urljoin`.
  - Save it as `NN.<ext>` (2 digits, extension from the URL, `.jpg` if there is none).
  - Remove `srcset`. On a fetch error, keep the remote `src` and add `data-missing="1"`.
- **`protect_math`:**
  - Each `<math>` inside `.MJX_Assistive_MathML` or `mjx-assistive-mml` becomes the text token `⟦m{n}⟧`, with the math stored in the table.
  - The rendered siblings (`.MathJax`, `.MathJax_Preview`, `mjx-container` visuals) are removed.
  - `<script type="math/tex">` is removed.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_source.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add magazine/source.py tests/test_source.py
git commit -m "feat: numbered source blocks, local images, protected math"
```

---

### Task 3: Capturing web pages

**Files:**
- Create: `magazine/capture.py`
- Modify: `magazine/__main__.py` (the `start` subcommand)
- Test: `tests/test_capture.py`

**Interfaces:**
- Consumes:
  - From Task 1: `Entry`, `parse_inbox`, `slug_for`.
  - From Task 2: `number_blocks`, `localize_images`, `protect_math`, `restore_math`.
- Produces:
  - `kind_of(url: str) -> Literal["video","github","arxiv","pdf","html"]`
  - `looks_blocked(title: str, text: str) -> bool`
  - `capture_html(url: str, item_dir: Path, browser) -> dict`
  - `capture(entry: Entry, item_dir: Path, browser) -> dict`: dispatches on `kind_of`, catches every exception into `status="unreadable"`, always writes `meta.json`, and returns the meta.
  - `capture_all(entries: list[Entry], issue_dir: Path, force: bool = False) -> list[dict]`
  - The meta schema (`meta.json`): `{url, note, slug, kind, status: "ok"|"unreadable", reason, title, site, author, date, blocks: int, palette: [hex], fonts: [str], screenshot: "items/<slug>/screenshot.png"}`
  - `issue.json`: `{"number": int, "month": "YYYY-MM"}`

- [ ] **Step 1: Write the failing tests** in `tests/test_capture.py`

```python
def test_kind_of():
    assert kind_of("https://www.youtube.com/watch?v=x") == "video"
    assert kind_of("https://youtu.be/x") == "video"
    assert kind_of("https://github.com/anthropics/original_performance_takehome") == "github"
    assert kind_of("https://github.com/a/b/blob/main/x.py") == "html"
    assert kind_of("https://arxiv.org/abs/2301.13142") == "arxiv"
    assert kind_of("https://arxiv.org/pdf/2301.13142v2") == "arxiv"
    assert kind_of("https://x.org/paper.PDF") == "pdf"
    assert kind_of("https://codeforces.com/contest/1953/problem/A") == "html"

def test_looks_blocked():
    assert looks_blocked("Just a moment...", "Checking your browser")
    assert looks_blocked("Example", "Enable JavaScript to continue")
    assert not looks_blocked("Problem - A - Codeforces", "x " * 400)

def test_capture_all_skips_existing(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(capture_mod, "capture",
        lambda e, d, b: calls.append(e.url) or (d.mkdir(parents=True, exist_ok=True),
            (d / "meta.json").write_text('{"url": "%s"}' % e.url))[0] or {"url": e.url})
    (tmp_path / "chapters").mkdir(); (tmp_path / "chapters" / "01-a.html").write_text("mine")
    es = [Entry("https://a.com/one"), Entry("https://b.com/two")]
    capture_all(es, tmp_path); capture_all(es, tmp_path)
    assert calls == ["https://a.com/one", "https://b.com/two"]
    assert (tmp_path / "chapters" / "01-a.html").read_text() == "mine"
```

`capture_all` takes its browser from a `with sync_playwright()` it opens itself. The test patches `capture` and must not launch a browser: open the browser lazily, only when there is something to capture.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_capture.py -v`
Expected: FAIL with an ImportError.

- [ ] **Step 3: Implement `kind_of`, `looks_blocked`, `capture`, `capture_all`, and `capture_html` for the `html` kind**

- **`looks_blocked`:** true when the title or text matches `just a moment|attention required|enable javascript|access denied|verify you are human` (case-insensitive), or the text has fewer than 80 words.
- **`capture_html`:**
  1. Open a Playwright page at 1440 × 900, `wait_until="networkidle"` with a 45 s timeout, then scroll to the bottom in steps to trigger lazy images.
  2. Save a full-viewport `screenshot.png`.
  3. Read the page style with `page.evaluate`: the computed `color` and `background-color` of `body`, `h1`, `h2`, `a` and the 5 largest visible elements, unique and turned into hex, as `palette`; the computed `font-family` of `body`, `h1` and `code`, as `fonts`.
  4. `protect_math(page.content())`.
  5. `trafilatura.extract(html, output_format="html", include_images=True, include_tables=True, include_formatting=True, include_links=True, with_metadata=False)` for the body, and `trafilatura.extract_metadata` for `title`, `site`, `author`, `date`.
  6. `restore_math`, then `localize_images(..., rel_prefix=f"items/{slug}/img/")`, then `number_blocks`.
  7. Write `source.html`.
  8. If `looks_blocked`, set `status="unreadable"` and `reason="blocked or empty page"`.
- **`capture_all`:**
  - Create `issue_dir/items/`, and write `issue.json` if it's missing. The number is the count of existing `issues/*/issue.json` plus 1.
  - Skip any entry whose `items/<slug>/meta.json` exists, unless `force` is set. Slugs come from `slug_for` in entry order.
  - Return the metas of all entries.
- **`start` subcommand:** `python -m magazine start [--month YYYY-MM] [--force]`. The month defaults to today. It parses `inbox.md`, runs `capture_all`, and prints one line per item: `slug  kind  status  blocks  reason`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_capture.py -v`
Expected: 3 passed.

- [ ] **Step 5: Live smoke check**

Put `- https://10-411.com` and `- https://codeforces.com/contest/1953/problem/A` in a scratch inbox. Run `uv run python -m magazine start --month 2000-01`.
Expected:
- Both items have `status: ok` and `blocks > 20`.
- The Codeforces `source.html` contains `<math` and the "Scoring" heading.
- `screenshot.png` opens.

Then delete `issues/2000-01`.

- [ ] **Step 6: Commit**

```bash
git add magazine tests
git commit -m "feat: capture web pages with full text, images, style and screenshot"
```

---

### Task 4: Capturing papers, PDFs, repos and videos

**Files:**
- Modify: `magazine/capture.py`
- Test: `tests/test_capture_kinds.py`

**Interfaces:**
- Consumes: Task 3's `capture_html` and the meta schema; Task 2's `number_blocks` and `localize_images`.
- Produces:
  - `arxiv_id(url: str) -> str | None`
  - `pdf_paragraphs(text: str) -> list[str]`
  - `vtt_to_paragraphs(vtt: str) -> list[str]`
  - `readme_base(owner: str, repo: str, branch: str) -> str`
  - `capture_arxiv`, `capture_pdf`, `capture_github`, `capture_video`, each with the signature `(url: str, item_dir: Path, browser) -> dict`

- [ ] **Step 1: Write the failing tests** in `tests/test_capture_kinds.py`

```python
def test_arxiv_id():
    assert arxiv_id("https://arxiv.org/abs/2301.13142") == "2301.13142"
    assert arxiv_id("https://arxiv.org/pdf/2301.13142v2.pdf") == "2301.13142v2"

def test_pdf_paragraphs_joins_lines_and_hyphens():
    text = "Self-compressing net-\nworks shrink\nthemselves.\n\nSecond para.\n\x0c3\n"
    assert pdf_paragraphs(text) == ["Self-compressing networks shrink themselves.", "Second para."]

def test_vtt_to_paragraphs_drops_timing_and_repeats():
    vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nhello there\n\n00:00:02.000 --> 00:00:03.000\nhello there\nhow are you\n"
    assert vtt_to_paragraphs(vtt) == ["hello there how are you"]

def test_readme_relative_images():
    base = readme_base("anthropics", "original_performance_takehome", "main")
    assert base == "https://raw.githubusercontent.com/anthropics/original_performance_takehome/main/"
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_capture_kinds.py -v`
Expected: FAIL with an ImportError.

- [ ] **Step 3: Implement**

- **`arxiv`:** try `capture_html(f"https://arxiv.org/html/{id}")`. If that is unreadable, fall back to `capture_pdf(f"https://arxiv.org/pdf/{id}")`. Keep the original `url` in meta.
- **`pdf`:**
  - Download the file to `item_dir/source.pdf`.
  - `pdftotext -enc UTF-8` → `pdf_paragraphs` → `<p>` blocks.
  - `pdfimages -png -p` → `img/`, skipping images under 150 px on either side. These are appended as `<figure>` blocks after the paragraphs of their page.
  - `pdftoppm -png -r 110 -f 1 -l 1` → `screenshot.png`.
  - `pdf_paragraphs` splits on blank lines and form feeds, drops lines that are only a page number, joins wrapped lines with a space, and joins a line ending in `-` straight onto the next line.
- **`github`:**
  - Read `GET https://api.github.com/repos/{o}/{r}` for `description`, `default_branch` and `stargazers_count`.
  - Read the README with `GET /repos/{o}/{r}/readme` and `Accept: application/vnd.github.html`.
  - `localize_images` with `base_url=readme_base(o, r, branch)`.
  - The first block is a `<p class="repo-meta">` holding the description, stars and URL.
  - Take the screenshot by loading the repo page.
- **`video`:**
  - `yt-dlp --skip-download --write-info-json --write-auto-subs --write-subs --sub-langs "en.*,es.*" --sub-format vtt --write-thumbnail -o item_dir/v`
  - `vtt_to_paragraphs` → `<p>` blocks. Start a new paragraph after a gap of more than 2 s, or every 80 words.
  - The thumbnail becomes `screenshot.png`; `title` and `author` come from the info json.
  - If there are no subtitles: `status="unreadable"`, `reason="no transcript"`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_capture_kinds.py -v`
Expected: 4 passed.

- [ ] **Step 5: Live smoke check**

Capture into a scratch month:
- `https://arxiv.org/abs/2301.13142`
- `https://github.com/anthropics/original_performance_takehome`
- one YouTube talk with captions

Expected:
- All three `status: ok`.
- The paper's `source.html` has its section headings and figures in `img/`.
- The README images point at local files.
- The transcript reads as paragraphs.

Delete the scratch month afterwards.

- [ ] **Step 6: Commit**

```bash
git add magazine tests
git commit -m "feat: capture arXiv papers, PDFs, GitHub repos and video transcripts"
```

---

### Task 5: Reader and assembly

**Files:**
- Create: `magazine/reader/reader.css`, `magazine/reader/reader.js`, `magazine/assemble.py`
- Modify: `magazine/__main__.py` (the `assemble` subcommand)
- Test: `tests/test_assemble.py`

**Interfaces:**
- Consumes: Task 2's block format (`data-b`) and the `items/<slug>/source.html` layout.
- Produces:
  - `expand_sources(chapter_html: str, items_dir: Path) -> str`. `<x-src item="S" from="A" to="B"></x-src>` becomes blocks A..B inclusive, and `<x-src item="S" b="N"></x-src>` becomes block N. Each inserted block gets `data-src="S"`. An unknown item or an out-of-range block raises `ValueError` naming the item and range.
  - `assemble(issue_dir: Path) -> Path`. It:
    - concatenates `chapters/*.html` in name order, expanding each chapter;
    - wraps the result in a skeleton: `<!doctype html>`, `<meta charset>`, `<title>Issue {number} · {Month YYYY}</title>`, links to `reader.css` then `style.css`, `<main class="deck">…</main>`, and `<script src="reader.js">`;
    - copies `reader.css` and `reader.js` into the issue;
    - writes `index.html` and returns its path.
  - The contract Claude writes against: each spread is `<section class="spread" data-item="SLUG">`. The cover, contents and back spreads use `data-item="_cover"`, `"_contents"` and `"_back"`.

- [ ] **Step 1: Write the failing tests** in `tests/test_assemble.py`

```python
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
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_assemble.py -v`
Expected: FAIL with an ImportError.

- [ ] **Step 3: Implement the reader and the assembly**

- **`reader.css`:**
  - `.spread` is exactly 1600 × 1000 px, `position: relative`, `overflow: hidden`.
  - `.deck` stacks spreads and is scaled by JS.
  - Print: `@page { size: 16in 10in; margin: 0 }`, each `.spread` gets `break-after: page`, and in print the scale is reset so 1600 px maps to 16 in.
- **`reader.js`:**
  - Shows one spread at a time, scaled to fit the window, centered on a dark desk.
  - Keys: → / Space / PageDown go forward, ← / PageUp go back, Home and End jump to the ends.
  - The current spread lives in `location.hash` as `#s{n}` (1-based), so reload keeps your place.
  - No dependencies.
- **`expand_sources`:**
  - Find tags with a regex on the fixed syntax `<x-src\s+([^>]*)></x-src>`.
  - Read blocks from `source.html` with lxml and serialize them with `lxml.html.tostring`.
  - Cache each item's blocks.

Wire `python -m magazine assemble [month]` (the month defaults to the latest).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_assemble.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add magazine tests
git commit -m "feat: spread reader and issue assembly with verbatim source expansion"
```

---

### Task 6: Checking an issue

**Files:**
- Create: `magazine/check.py`
- Modify: `magazine/__main__.py` (the `check` subcommand)
- Test: `tests/test_check.py`

**Interfaces:**
- Consumes: Task 5's `index.html` contract (`.spread[data-item]`, `[data-src][data-b]`) and Task 3's `meta.json`.
- Produces:
  - `placement_problems(index_html: str, items_dir: Path) -> list[str]`. It reports:
    - for every item with `status: ok`, each block number from 1 to `blocks` that is missing or placed more than once, compressed into ranges (`"codeforces-…: blocks 41–58 missing"`);
    - every captured slug (`ok` or `unreadable`) that has no `.spread[data-item=slug]`.
  - `render_problems(index: Path, proofs_dir: Path | None = None) -> list[str]`. Using Playwright at a 1600 × 1000 viewport, it reports:
    - each spread whose `scrollHeight` or `scrollWidth` exceeds its size by more than 1 px, or that holds an element whose bounding box sticks out past the spread (`"spread 7 (paper-x): overflows by 212px"`);
    - each `img` with `naturalWidth == 0`.
    - With `proofs_dir`, it also saves `proofs/{n:02}.png` per spread.
  - `check(issue_dir: Path, shots: bool = False) -> list[str]`
  - CLI: `python -m magazine check [month] [--shots]` prints the problems and exits 1 if there are any, else prints `ok`.

- [ ] **Step 1: Write the failing tests** in `tests/test_check.py`

```python
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
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_check.py -v`
Expected: FAIL with an ImportError.

- [ ] **Step 3: Implement `magazine/check.py`**, and wire the CLI.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add magazine tests
git commit -m "feat: check issues for missing source text, overflow and broken images"
```

---

### Task 7: House style and the `/issue` skill

**Files:**
- Create: `policies.md`, `.claude/skills/issue/SKILL.md`

**Interfaces:**
- Consumes: the CLI subcommands `start`, `assemble`, `check --shots` and `archive`; the `<x-src>` and `.spread[data-item]` contract; the meta schema.

- [ ] **Step 1: Write `policies.md`**

Write it as the editor's style guide, in plain prose with one heading per guideline. Carry over every guideline from the spec's "The house style" section, plus:
- **Two voices:** source words only via `<x-src>`; Claude's words only in `.editor`, set in a visibly different voice.
- **Every item in full.**
- **Unreadable items** get a small entry saying why, with the link.
- **The front:** the same every issue (as `mockups/covers.html`, cover E):
  - `chapters/00-cover.html` is one spread showing `../../assets/front.jpg` at full size, with `object-fit: cover`.
  - `PROJECTIONS` is set in Cormorant Garamond, 48px, uppercase, letter-spacing .07em. It is centred at x = 1200, with its top at 493px.
  - Under it, `Nº NN · MONTH YEAR` (the year in Roman numerals, e.g. `Nº 01 · NOVEMBER MMXXVI`), 19px, letter-spacing .16em, top at 551px.
  - Nothing else goes on it.
- **Principles, not imitation:** apart from the front, the portfolio is a reference for principles; never reproduce its work.

State at the top that these are guidelines to apply with judgment, not rules.

- [ ] **Step 2: Write `.claude/skills/issue/SKILL.md`**

Frontmatter: `name: issue`, `description: Make this month's magazine issue from inbox.md`. Body, in order:

1. Run `uv run python -m magazine start`, report the capture table, and ask before continuing if more than a third of the items are unreadable.
   - **Resolving a front page.** If an entry points at a site's front page or an index, and its note names one specific piece (for example, `[crawling a billion pages](https://andrewkchan.dev/)`), open the page, find the link whose text matches the note, and re-run capture for that URL into the same slug with `start --force`. Record both URLs in `meta.json` (`url` and `saved_url`), and say on the opener "You saved the front page; this is the post it pointed to."
2. Read `policies.md`. If a previous issue exists, read its `style.css` and two of its chapters as the reference for the frame.
3. For each item, read `meta.json`, look at `screenshot.png`, and skim `source.html` (block count, headings, figures) to learn its world.
4. Write `issues/<month>/plan.md`: the order, the spreads per item with the block ranges each spread holds, and what sits next to what.
5. Write `style.css` (the frame, which is the house), then `chapters/00-cover.html`, `01-contents.html`, `NN-<slug>.html` per item, and `99-back.html`.
   - Each item's own world goes in a `<style>` inside its chapter, scoped by `[data-item="<slug>"]`.
   - Source text appears only through `<x-src>`.
   - With more than 8 items, write the frame and cover yourself, then hand chapters to parallel subagents. Each gets `policies.md`, `style.css`, its item folder and the `<x-src>` contract.
6. Loop until `check --shots` prints `ok`:
   - run `uv run python -m magazine assemble`, then `uv run python -m magazine check --shots`;
   - fix every problem by moving block ranges between spreads or adding spreads, never by cutting text;
   - look at `proofs/*.png` and fix what reads badly against `policies.md`.
7. Tell the user the issue is ready at `issues/<month>/index.html`. Run `uv run python -m magazine archive` only after they confirm.

- [ ] **Step 3: Commit**

```bash
git add policies.md .claude/skills/issue/SKILL.md
git commit -m "feat: house style and /issue skill"
```

---

### Task 8: The first real issue

**Files:**
- Modify: `inbox.md`
- Create: `issues/2026-11/…`, written by the skill

- [ ] **Step 1: Fill the inbox** with the links from this project's conversation:
  - `https://codeforces.com/contest/1953/problem/A`
  - `https://10-411.com`
  - `https://arxiv.org/abs/2301.13142`
  - `https://github.com/anthropics/original_performance_takehome`

  Also ask the user for any links they want added before running.

- [ ] **Step 2: Run `/issue` in Claude Code inside the repo**

Expected:
- `check` prints `ok`.
- `issues/2026-11/index.html` opens in the browser on the front (the drawing, with `PROJECTIONS / Nº 01 · NOVEMBER MMXXVI`). Arrow keys turn spreads, and each item looks like itself inside the shared frame.

- [ ] **Step 3: Print preview**

Open the issue in the browser's print preview.
Expected: one spread per 16 × 10 in page, and nothing clipped.

- [ ] **Step 4: Hand it to the user to read**, and record what they want changed in `policies.md`. Commit:

```bash
git add inbox.md issues/2026-11 policies.md
git commit -m "issue: No. 1, November 2026"
```
