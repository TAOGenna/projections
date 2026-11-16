# The Projections site — design

Date: 2026-11-15, revised 2026-11-16 · Status: built on the `site` branch, iterated with the owner

## Intent

A public page that shows people what Projections is by letting them open a real issue, and tells them how to set it
up with their own agent. Made from the magazine's own visual ideas, after Taili Zhuang's portfolio: one composed
page, the words in a box, the work shown as an object.

## Decided

- **A standalone static site** in this repo, `site/`: plain HTML/CSS/JS, no build step, published later by the repo's
  GitHub Pages at taogenna.github.io/projections. `site/index.html` is the landing.
- **One page, no scrolling.** A fixed 1600 × 1000 composition scaled to the window (`landing.js`); the ground, the
  imprinted drawing, the light and the grain fill the whole window around it, so no edge shows on any shape.
  - **The ground:** teal, the portfolio's bridge sheets. Its colours are one list of variables at the top of the page.
  - **The imprint:** the cover's drawing across the whole page, its lines only (`landing/lines.webp`, a mask with the
    drawing's own box erased), so it takes any colour on any ground.
  - **The box,** frosted glass the drawing shows through: the name; the tagline "A magazine your agents make from
    what you save and bookmark"; "An agent skill"; three steps (Save, Run, Read), one line each; the setup commands
    on their own inset, highlighted, with Copy.
  - **The issue as a printed magazine** (`landing/magazine.js`): it floats closed on its cover, opens in place on a
    click or Enter, and turns page by page with clicks or the arrows; each page is a leaf of curved strips shaded by
    one light. Its page images are rendered from the sample by `gen_sample.py pages` into `landing/pages`, loaded as
    they are reached. "Full screen" opens the reader over the page at the same spread.
- **The copy speaks of agents, not Claude,** and of no fixed schedule (the owner's calls, 2026-11-16).
- **Assets are versioned by their content** (`?v=` on the page's CSS, scripts and page images), so a change always
  reaches a browser.
- **A sample issue** (Nº 00) made by the real pipeline from three pieces of the owner's own reading list: Sophie
  Wang's "JPEG compression", Jeremy Bernstein's "Deriving Muon" and Seb-V's "Optimizing Matrix Multiplication on
  RDNA3". The owner decided (2026-11-15) that licences don't gate the sample; every piece is credited by author and
  link on its opener and in the colophon. Its generator is `site/making/gen_sample.py`.

## Constraints

- **The front is the magazine's own cover** (the owner's call, 2026-11-15): Taili Zhuang's portfolio drawing, as on
  Nº 01, as `site/cover.jpg`, on the sample's cover and imprinted across the landing. The front stays clean, with no
  credit line; he is credited in the sample's colophon. The openers' drawings are our own.
- **The repo will be public.** Each month's `issues/` content stays out of it.

## Not yet

- Phones: the composition scales down as a whole; a layout of its own for narrow screens is still to come.
