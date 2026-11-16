---
name: issue
description: Make this month's magazine issue from inbox.md
---

# Make this month's issue of Projections

You are the editor and the designer. You capture every link in `inbox.md`, then write the whole issue yourself as HTML, following `policies.md`. Code only does what you must not do by hand: capturing, placing the source's text verbatim, and checking.

Run everything from the repo root. `<month>` is `YYYY-MM` (default: this month).

## The contract

- The issue lives in `issues/<month>/`. Each captured item is in `items/<slug>/`:
  - `meta.json`: url, note, kind, status, reason, title, site, author, date, block count, palette, fonts;
  - `source.html`: the full text as numbered blocks (`data-b="1".."n"`);
  - `screenshot.png`;
  - `img/`: the item's images, referenced in `source.html` as `items/<slug>/img/NN.ext`.
- You write `style.css` and `chapters/*.html`. They are concatenated in name order: `00-cover.html`, `01-contents.html`, `NN-<slug>.html` per item, `99-back.html`.
- Every spread is `<section class="spread" data-item="SLUG">…</section>`, 1600 × 1000 px. The cover, contents and back use `data-item="_cover"`, `"_contents"` and `"_back"`. Every captured item (readable or not) needs at least one spread with its slug.
- The source's words appear only through `<x-src item="SLUG" from="A" to="B"></x-src>` or `<x-src item="SLUG" b="N"></x-src>`. Assembly replaces each with those blocks, verbatim. Never type the source's words yourself.
- Your own words always sit inside an element with class `editor`.
- Every page number is printed in an element with class `folio`, two pages to a spread, the front being pages 0–1. The reader finds a typed page number by these.
- Every page but the openers carries running heads: `<div class="runhead l">Projections · Nº NN</div>` on the left page and the chapter's title in `runhead r`. The reader makes the left one, the masthead, a way back to the contents.
- Each contents row links to its chapter's first page: `<a href="#p<page>">`. Make the row's numeral and title links, both to the page the row prints.
- An image that couldn't be downloaded keeps its original link and `data-missing="1"`. Leave it placed: the check doesn't count it as broken.
- Paths in chapters are relative to `issues/<month>/`: item images are `items/<slug>/img/…`, and the front drawing is `../../assets/front.jpg`.

## Steps

1. **Capture.** Run `uv run python -m magazine start`. A page behind a human check (Codeforces) is read through the user's Safari: a tab opens for a few seconds; the first time, macOS asks to let the terminal control Safari, and a check, if Safari shows one, is the user's to click. Report the table it prints (slug, kind, status, blocks, reason). If more than a third of the items are unreadable, ask the user before continuing.
   - **Resolving a front page.** An entry may point at a site's front page or an index while its note names one specific piece, for example `[crawling a billion pages](https://andrewkchan.dev/)`. Open the page, find the link whose text matches the note, and run `uv run python -m magazine recapture <slug> <that-url>`. It captures the piece into the same folder and keeps the saved link as `saved_url`. On the item's opener, say: "You saved the front page; this is the post it pointed to."
2. **Read the house style.** Read `policies.md`. If a previous issue exists in `issues/`, read its `style.css` and two of its chapters, and keep its frame.
3. **Study each item.** Read its `meta.json`, look at `screenshot.png`, and skim `source.html`: the block count, the headings, the figures, the kind of structure. Learn its world: colours, imagery, texture, structure. (Type is the house's: see `policies.md`.)
4. **Plan.** Write `issues/<month>/plan.md`:
   - the order of the items, and what sits next to what;
   - for each item, its spreads and the block range each spread holds, so that every block from 1 to n is placed exactly once;
   - the one big image of each chapter.
5. **Write the issue.**
   - Write `style.css`: the house frame and the house type for all text (see `policies.md`), the numeral, the hairline box, titles, subtitles, source block, `.editor`, captions, keys, running heads, page numbers).
   - Write `chapters/00-cover.html` exactly as `policies.md` describes the front, then `01-contents.html`.
   - Write `NN-<slug>.html` for each item. Put the item's own world (never its fonts) in a `<style>` inside its chapter, scoped by `[data-item="<slug>"]`.
   - An opener is a visual invitation, not a summary (`policies.md`, "The opener is an invitation"): words only in the box; outside it, the piece's own pictures and your drawn objects, large and at scale, with at most a two-line label naming each. No keys, quoted sentences, formulas, numbers or annotations on an opener.
   - A contest problem (Codeforces, AtCoder…) gets a plain opener: the frame on a quiet ground, no art, no editor's note, and the statement starting on its right page.
   - Give each opener a ground made from its item's own material, and set its tones (`policies.md`, "Grounds and tones"). Decoration is `aria-hidden`.
   - Write `99-back.html`: an "unreadable" list with links, if any, and the colophon.
   - With more than 8 items, write the frame, the cover and the contents yourself, then hand chapters to parallel subagents. Give each one `policies.md`, `style.css`, its item folder, its block ranges from `plan.md`, and this contract.
6. **Assemble and check, until it prints `ok`.**
   - Run `uv run python -m magazine assemble`, then `uv run python -m magazine bake` (heavy decoration becomes images, so turning pages stays smooth), then `uv run python -m magazine check --shots`.
   - Fix every problem by moving block ranges between spreads or adding spreads. Never cut text.
   - Look at `proofs/*.png`, one per spread, and fix whatever reads badly against `policies.md`: cramped columns, orphaned headings, a frame that drifted, an item that lost its world.
7. **Hand it over.** Run `uv run python -m magazine open` to open the issue in the user's browser, and tell them it is at `issues/<month>/index.html` (← → turn spreads) and that `uv run python -m magazine open` brings it back any time, at the spread they stopped on (`open YYYY-MM` for an earlier issue). Only after they confirm, run `uv run python -m magazine archive` to move the used lines out of `inbox.md`.

## Never

- Sign in anywhere, or get around a paywall, a login or a bot check. A blocked item gets a stub entry.
- Alter the source's text, or drop part of it.
- Commit `assets/front.jpg`.
