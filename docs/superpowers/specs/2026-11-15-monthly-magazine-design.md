# A monthly magazine of what you saved — design

Date: 2026-11-15 · Status: approved · Name of the magazine: **Projections**

## Intent

You keep running into things worth keeping: an article, a paper, a problem, a syllabus, a repo, a video. They pile up and you never sit down with them.

This turns that pile into a magazine you actually want to read. Once a month you run it, and Claude reads everything you saved and lays it out as an issue you read on your computer, one spread at a time, the way you'd read a printed magazine. Each thing appears in full, so the issue replaces opening the links. It should be a delight to read, the way Taili Zhuang's 2020 architecture portfolio is (`~/Downloads/Taili-Zhuang-Portfolio-2020.pdf`).

It's like getoffprint.com (read-it-later, printed and mailed monthly), but it's not a service. It's a repo plus a Claude Code skill that runs on your own computer with your own Claude. It's for you first; if it works for you, it's the starting point for anyone else.

"Projecting" is the core idea. Each thing you save gets captured faithfully (content, images, layout, structure) and projected into the magazine. The projection isn't uniform: each item keeps as much of its own identity as possible, while still clearly belonging to your magazine.

## Goals

- A monthly issue you read on a computer like a magazine: landscape spreads, one at a time, turned with the keyboard.
- Every item is in the issue **in full**: its whole text, its images, its structure.
- Saving is as cheap as pasting a link into a markdown file.
- Each item keeps its own world (colors, imagery, texture, kind of structure) inside one recurring house frame.
- The house style lives in a file you write and evolve (`policies.md`). Claude follows it as general guidelines, not hard rules.
- It can be printed, but screen comes first.

## Non-goals (for now)

- ChatGPT, Codex or any assistant other than Claude Code.
- Other people's setups: no installer, no onboarding, no configuration for strangers.
- Printing and shipping, payments, accounts, a hosted service, a server.
- X bookmarks, or anything built around X. You give the links directly, pointing at the thing itself rather than a post that wraps it.
- Logins and paywalls. You give links Claude can open. Capture doesn't sign in anywhere. A page behind a human check (Codeforces) is read through your own Safari, with your session, as your contest scripts do; capture never solves the check itself.
- A backlog. The first issue starts from what you add from now on.

## Anti-goals: it fails if…

- It reads like reader mode or a feed: every item flattened into the same text column.
- Items get forced into a few fixed templates, so the bridge chapter looks like the theatre chapter.
- Claude's words get mixed up with the source's. The reader must always know whose words they're reading.
- The source's text gets altered: retyped with mistakes, paraphrased, or silently shortened.
- It copies the portfolio's actual work or identity, beyond the one exception you chose (the front, below). The portfolio is the reference for *principles* (frame, rhythm, captions, worlds), not something to imitate.
- Running an issue needs anything beyond Claude Code on your computer.

## How it works

### 1. Saving (any time during the month)

One markdown file, the inbox. One line per thing: a link, plus a note only if you want one. About 15–20 items a month.

```md
- https://arxiv.org/abs/2301.13142 — the compression trick
- https://codeforces.com/contest/1953/problem/A
- https://github.com/anthropics/original_performance_takehome
```

Anything with a link counts: web pages, articles, PDFs, papers, repos, videos, problem statements.

### 2. Making the issue (once a month, run by hand)

You run the `/issue` skill in Claude Code inside the repo. Claude:

1. Reads `policies.md` and the inbox.
2. Captures each item into the issue's folder: its full text, images, screenshots of how it looks, its palette and type, its structure.
3. Decides the order and what sits next to what, following `policies.md`.
4. Writes the whole issue itself as HTML (approach A, below): cover, contents, one chapter per item, back matter. Each chapter runs as many spreads as the item needs to appear in full.
5. Moves the used lines out of the inbox into the issue's record, so next month starts empty.

### 3. Reading

You open the issue in your browser. One landscape spread per screen; arrow keys turn spreads. It prints as spreads if you ever want paper.

## The house style (`policies.md`)

`policies.md` is the editor's style guide. These are the starting guidelines, taken from what makes the portfolio a delight to read. You'll edit them over time.

- **The frame stays constant.** Every chapter opens the same way: a large numeral breaking the top edge of a thin hairline box, the title in spaced serif capitals, a one-line italic subtitle, a small source block (where it's from, author, date), and a short block of text.
- **Captions follow one convention.** Line one says what the image is. Line two, lighter, says what kind of thing it is or where it comes from.
- **Numbered keys.** Numbers on an image tie to a numbered list beside it.
- **Each item keeps its own world inside the frame.** The background, palette, texture and kind of imagery come from the item. The frame comes from the house.
- **Rhythm.** A chapter goes opener → the item in full → one big image. The item's own text is never cut. Claude's own words stay few, and pictures carry the pacing between stretches of text.
- **Two voices.** The source's words appear exactly as written. Claude's words (the opener's short text, notes linking items) are set apart in a distinct editor's voice.
- **Room follows the item.** A short post might take part of a spread; a paper takes as many spreads as its full text and figures need.
- **Spreads are landscape**, sized to a laptop screen.

## Approaches considered

The question was who designs each spread: Claude or a template.

- **A. Claude writes everything, every month (chosen).** The skill has Claude capture every item and write the whole issue by hand.
  - Gives each item the most freedom to keep its identity, and every issue is its own object.
  - Costs: the frame can drift between issues; fixing one chapter means editing the issue; long issues are slower and use more tokens.
- **B. Capture scripts plus fixed spread templates.** Claude only picks a template per item and a renderer builds the issue.
  - Consistent and cheap.
  - Rejected: it flattens items into a few shapes, which is the main anti-goal.
- **C. A fixed frame in code, with Claude writing free chapters stitched by a build step.**
  - Keeps the frame identical month to month and lets you redo one chapter at a time.
  - Not chosen: you preferred Claude owning the whole issue, with the frame held by guidelines rather than code.

## Decided

- Claude Code only; one user (you).
- Approach A: Claude captures and writes the whole issue every month.
- Monthly, run by hand with a skill; about 15–20 items an issue; no backlog.
- Every item appears in full.
- The inbox is one markdown file of links you choose, with optional notes; nothing X-specific.
- Computer first: landscape spreads, keyboard navigation, printable.
- `policies.md` holds the house style as guidelines Claude follows with judgment.
- The portfolio's principles (above) are the starting house style.
- The magazine is called **Projections**.
- One type throughout, Taili Zhuang's: Garamond capitals for headings, light Open Sans for the text (upright for the sources, italic for the editor). Each item keeps its colours, imagery and structure, not its fonts. (Chosen after comparing both versions of Nº 01.)
- The front is the same every issue: the portfolio's front-page drawing with Taili Zhuang's name erased, and "PROJECTIONS / Nº NN · MONTH YEAR" set where his name was (mockup: `mockups/covers.html`, cover E). It's his work, so it stays in your copy only: the image is never committed and never ships with the repo.

## My calls (for you to check)

- **Inbox location.** It's `inbox.md` at the repo root.
- **Issue format.** Each issue is a folder, `issues/YYYY-MM/`, with `index.html`, an `assets/` folder of captured images, and the captured sources it was made from. I chose a folder over a single file with images embedded inside it, because issues with full papers and many images would get very large.
- **No retyping.** Capture saves each source's full text to disk. When writing the issue, Claude places that captured text rather than retyping it from memory, so the source's words reach the page unchanged.
- **Writing chapter by chapter.** Fifteen to twenty items in full is more than one pass of Claude can write comfortably. Under A, Claude may write each chapter separately (using parallel helpers if needed) and then assemble the issue. Claude still writes everything; no templates are added.
- **Keeping the frame steady.** Before writing a new issue, Claude reads the previous one as a reference for the frame, so drift stays small without moving the frame into code.
- **Unreadable links** (dead link, blocked site) get a small entry that says so and keeps the link, rather than being dropped silently.
- **The old experiments** (`fetch_bookmarks.py`, `issue/`, `proofs/`, `OFFPRINT.md`) and the design mockups were removed on 15 November 2026, once Nº 01 replaced them as the reference.

## Left to the builder

- Capture tooling: a headless browser or plain downloads for pages, images and screenshots; PDF text and figure extraction for papers.
- How videos are projected (transcript, key frames, a storyboard) and what that needs installed.
- How long text flows across fixed-size landscape spreads (columns, continuation, page numbers).
- Spread size and aspect, fonts, and print CSS, all within the guidelines above.
- The skill's exact wording and file layout, and how the issue's record of used inbox lines is stored.
