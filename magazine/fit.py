"""Fitting an item's blocks into column boxes: how many go in each, measured in the real assembled page."""
from pathlib import Path

from magazine.assemble import expand_sources

# Adds blocks to an empty box of the given class, in a spread of the item (so its scoped world applies), until one
# no longer fits; returns how many did. A first block too big for the box still counts, so the fit always moves on.
FIT_JS = """([slug, cls, blocks]) => {
  const host = document.createElement('section');
  host.className = 'spread __check'; host.dataset.item = slug;
  document.querySelector('.deck').appendChild(host);
  const box = document.createElement('div'); box.className = cls; host.appendChild(box);
  const over = () => box.scrollWidth > box.clientWidth + 1 || box.scrollHeight > box.clientHeight + 1;
  let n = 0;
  for (const html of blocks) {
    const t = document.createElement('template'); t.innerHTML = html; box.appendChild(t.content.firstElementChild);
    if (over()) { if (n === 0) n = 1; break; }
    n++;
  }
  host.remove();
  return n;
}"""
ONE = ".deck{position:static!important;transform:none!important} .spread{display:none!important} .spread.__check{display:block!important}"
FACES = ['300 14px "Open Sans"', '400 14px "Open Sans"', '600 14px "Open Sans"', 'italic 300 14px "Open Sans"',
         '400 20px "Cormorant Garamond"', '500 20px "Cormorant Garamond"']


def fit(issue_dir: Path, slug: str, first: int, last: int, box: str = "flow pair W") -> list[tuple[int, int]]:
    """The block ranges, first to last, that fill one box each. Assemble once before, so the item's style is there."""
    from playwright.sync_api import sync_playwright

    blocks = [expand_sources(f'<x-src item="{slug}" b="{n}"></x-src>', issue_dir / "items") for n in range(first, last + 1)]
    out, n = [], first
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1600, "height": 1000})
        pg.goto((issue_dir / "index.html").resolve().as_uri(), wait_until="load")
        pg.add_style_tag(content=ONE)
        pg.evaluate(f"Promise.all({FACES!r}.map(f => document.fonts.load(f)))")  # a fallback face packs more
        while n <= last:
            got = pg.evaluate(FIT_JS, [slug, box, blocks[n - first:]])
            out.append((n, n + got - 1))
            n += got
        b.close()
    return out
