# Projections — house style

These are the editor's guidelines for making each issue: a delight to read, modelled on the principles of Taili Zhuang's 2020 portfolio. Apply them with judgment. They are not rules, and when one gets in the way of an item reading well, the item wins. Edit this file as the magazine finds its voice.

## The magazine

Projections is a monthly magazine of the things you saved, each one projected into the issue: captured faithfully, keeping its own identity, and set inside one recurring house frame. You read it on a computer, one landscape spread at a time, like a printed magazine. It also comes as a PDF of single pages, for reading where a spread is too small to zoom into.

## Spreads are landscape, and every page stands alone

Every spread is 1600 × 1000 px: two 800 px pages side by side, on a laptop-shaped screen. Design each spread as a
whole, but the PDF cuts it at the gutter into its two pages, so each page must read on its own:
- **Content never crosses the gutter.** No line of text, column, figure, table, code block or caption runs across
  800 px. Text sits in columns that belong to one page (`.flow.l`, `.flow.r`), never in one column box across both.
- **Each page is centred on itself.** Its margins are the same on both sides: 60 px outside, and 60 px on the gutter
  side too. Text keeps out of the 60 px either side of the gutter.
- **A figure too big for a column takes a whole page.** Set it as large as the page allows, or let it bleed to the
  page's edges inside a box clipped at the page. If two columns would cramp a figure, a table or a stretch of text,
  give it the full page width instead. A figure is never split across two pages.
- **Only the ground may cross:** a ground, a texture, faint construction geometry or giant faint type can run across
  the gutter, as the seam the two pages share. Anything that reads as a picture stays on one page, even when it is
  drawn for the issue and `aria-hidden`: a diagram, a chart, a sequence of objects. Keep it 60 px clear of the gutter.
  The cover's picture is the one exception: the PDF keeps its right half as the front.

## The front

The front is the same every issue.
- `chapters/00-cover.html` is one spread (`data-item="_cover"`) showing `../../assets/front.jpg` over the whole spread, with `object-fit: cover`.
- `PROJECTIONS` is set in Cormorant Garamond, 48px, uppercase, letter-spacing .07em, centred at x = 1200, with its top at 493px.
- Under it goes `Nº NN · MONTH YEAR`, with the year in Roman numerals (`Nº 01 · NOVEMBER MMXXVI`): 19px, letter-spacing .16em, top at 551px.
- Nothing else goes on it. The drawing's own hairline box frames the name; don't draw another.

Reference: Nº 01's front (`issues/2026-11/chapters/00-cover.html`).

## The frame stays constant

Every chapter opens the same way:
- a large Roman numeral breaking the top edge of a thin hairline box;
- the title in spaced serif capitals (Cormorant Garamond);
- a one-line italic subtitle;
- a small source block: where it's from, the author, the date;
- a short block of the editor's text.

The frame lives in the issue's `style.css` and is the same from chapter to chapter and, as far as possible, from issue to issue. Before writing a new issue, look at the previous one's frame and keep it. Reference: Nº 01 (`issues/2026-11`).

## One type, Taili Zhuang's, throughout

Everything in the issue is set in the house's two faces, as in Taili Zhuang's portfolio:
- **Headings** of every item (h1–h6) in Cormorant Garamond, medium, uppercase, letter-spaced (about .08em).
- **The sources' text** in Open Sans Light (300), upright, justified and hyphenated, about 13.5px on a 1.6 line.
- **The editor's words** in Open Sans Light *italic*, which is the portfolio's text voice. Italic is reserved for
  the editor, so the reader always knows whose words they are reading.
- Load every weight and style the issue uses (Open Sans 300, 400 and 600 with their italics; Cormorant Garamond
  400 and 500). A weight that isn't loaded gets faked by the browser and looks like another typeface; the check
  reports it.
- Code stays monospace, and math stays math: formulas are MathML, drawn in a LaTeX-quality math font (Latin Modern
  Math when the reader has it, STIX Two Math otherwise). A PDF's display equations are cropped from its page as
  the author typeset them. A very dense item (a README, a reference list) may go a little
  smaller, never into another face.

## Each item keeps its own world inside the frame

Inside the frame, the item is itself in everything but type: its background, palette, texture, the kind of
imagery it uses, and the shape of its structure (a problem statement's boxed samples, a syllabus's ruled table, a
paper's figures and columns, an essay's plain column). Take these from the capture: `meta.json` (`palette`),
`screenshot.png`, and the markup of `source.html`. A Codeforces problem should still look like a Codeforces
problem, in the house's type. The frame and the type come from the house; the world comes from the item.

## The opener is an invitation

The opener is a visual invitation to the reading, not a summary of it. It makes you want to turn the page; it
doesn't explain what you're about to read. Look at the portfolio's openers: the words are all in the box, and
everything else is the work itself, large and at scale.
- **The words live in the box, and only there:** the numeral, the title, a subtitle, the credits, and the editor's
  short paragraph about the piece (what it is, not what its pictures show). The item's text starts on the next spread.
- **Outside the box, only images, at scale and in layers:**
  - a ground;
  - faint construction geometry (circles, a column grid) crossing everything;
  - the item's own pictures standing large on the ground and bleeding off the edges, like models on a shelf, or one
    framed like a print;
  - a sequence is welcome: the same thing again and again, growing or changing, like the portfolio's array of towers.
- **Labels name, never explain.** An object may carry a label of two short lines, small, at its foot: what it is,
  then what it's made of or where it's from (`The flamingos, five times` / `JPEG at falling quality, drawn for this
  issue`). Never a sentence from the reading, a caption that teaches, a numbered key, a formula, a number, an axis
  or an annotation. If a picture needs words to make sense, it belongs inside the reading, not on the opener.
- **Each chapter also gets its "one big image":** a whole page given to its strongest figure.
- **Except contest problems.** A competitive-programming problem (Codeforces, AtCoder and the like) gets a plain
  opener: the frame on a quiet ground, and nothing else. No drawing, figure or giant type, and no note that
  hints at a solution: no editor's note at all, since the source block already says where it's from. With nothing to
  compose, the right page isn't left blank: the statement starts there, as on a printed problem sheet.
  Plain is not neglected. The opener and every spread of the statement are printed on a good paper: a quiet tone
  from the site's own palette, with a faint field and a fine grain.
- **Every opener gets this care, whatever the item gives.** When an item has few or no pictures, the editor draws
  objects for it from its own material: a photograph at falling quality, a benchmark's results built as towers to
  scale, a mechanism's motion drawn as tracks. Drawings are objects, not diagrams: they show form, scale and
  repetition, with no labels on them, and never invent facts the item doesn't state.

## Grounds and tones

After the portfolio, where every chapter's background comes from the project's own making, never a generic texture.
- **Each opener gets a ground made from the item's own material.** Use one of these:
  - its figures, as a faint ghost, a duotone, or a chalk line drawing on a dark ground;
  - its palette, as a painted field: a palette colour through fractal noise, with grain;
  - its own words, set as faint giant type behind the numeral band;
  - a construction drawing of its idea, such as loops around a point for winding numbers.
- Never use stock textures, and never use the portfolio's own paintings, photographs or drawings.
- **One device per spread.** Decoration is `aria-hidden` and sits inside a clipping box. Keep it faint where text runs over it.
- **Tone.** Ink is the ground's opposite pole, mixed toward the ground so it takes the ground's hue:
  - the title and numeral at 85%, the text at 78%, the source line at 62%, the hairline at 50% (the tokens in `style.css`);
  - never pure white on dark;
  - a panel with its own ground (a dark page, a light veil, a card) carries `data-tone` and `--ground`;
  - the numeral has no knockout: the box's hairline runs behind it.
- **The flip.** Use the dark tone when the ground's luminance is at most 0.08, and the light tone when it's at least 0.39. In between, put a veil or a card under the text.
- **Rhythm.**
  - Alternate the openers' tones from chapter to chapter.
  - Give at most one chapter per issue a coloured moment, for example its diagram on a pale card over a painted field.
  - The opener box never moves, so everything around it can.
- **Which ground suits which kind of item:**
  - a plain-text page: its own words as faint giant type, plus a structural ruler (weeks, sections);
  - a math-heavy page: a dark slate with a chalk construction;
  - a repository: its own dark canvas (GitHub's) beside the light README;
  - a systems essay: its diagram as the coloured moment;
  - a paper: a quiet painted field in a warm neutral.
- Don't blur or duotone screenshots of text, invert colour renders, or put a plot where colour carries data under a filter.

## Every item in full

Each item appears in full: all of its text, its images and its structure. The issue replaces opening the link. Never cut, shorten or summarise the source to make it fit. If it doesn't fit, give it more room: another column or another spread.

## Two voices

The reader must always know whose words they are reading.
- The source's words reach the page only through `<x-src item="SLUG" from="A" to="B"></x-src>` (or `b="N"` for one block). They are placed exactly as captured. Never retype, paraphrase or "fix" them.
- The editor's words (Claude's) always sit inside an element with class `editor`: light italic Open Sans, set apart from the source. The opener's short text, notes linking items, and captions you write are the editor's.

## Captions follow one convention

Line one says what the image is. Line two, lighter and smaller, says what kind of thing it is or where it comes from (`a figure from III, p. 13`, `the post's own diagram`). On an opener, that is all a label ever says.

## Numbered keys

Inside the reading, when an image has parts worth naming, put small numbers on it and a numbered list beside it. Never on an opener.

## Rhythm

A chapter goes: opener → the item in full → one big image. The item's own text is never cut. The editor's words stay few. Pictures carry the pacing between stretches of text, and a dense page is followed by an open one.

## Room follows the item

A short post might take part of a spread. A paper takes as many spreads as its full text and figures need. Columns are the usual tool: one or two per page for long text, sized to the item's own type.

## Unreadable items

When a link couldn't be read (a dead link, a bot wall, a video with no transcript), it still gets a small entry with its own `data-item` spread, or part of one. Say plainly why it couldn't be read, and keep the link so it can be opened by hand.

## Bleeds

Anything meant to run off the edge of a spread (a big image, a drawing) goes inside a box with `overflow: hidden`. The check treats anything else that sticks out as lost content. A picture that bleeds stops at the gutter: its box is clipped at its own page.

## Principles, not imitation

Apart from the front, the portfolio is a reference for principles (the frame, the rhythm, the captions, the worlds), never something to copy. Don't reproduce its drawings, layouts or identity.
