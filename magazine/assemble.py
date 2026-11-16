"""Assembling an issue: Claude's chapters, with the sources' own blocks placed verbatim, wrapped in the reader."""
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

import lxml.html

READER = Path(__file__).parent / "reader"
X_SRC = re.compile(r"<x-src\s+([^>]*)></x-src>")
ATTR = re.compile(r'([\w-]+)="([^"]*)"')

SKELETON = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="reader.css">
<link rel="stylesheet" href="style.css">
</head>
<body>
<main class="deck">
{body}
</main>
<script src="reader.js"></script>
</body>
</html>
"""


def _blocks(slug: str, items_dir: Path, cache: dict) -> dict[int, str]:
    if slug not in cache:
        src = items_dir / slug / "source.html"
        if not src.exists():
            raise ValueError(f"x-src: unknown item {slug!r}")
        blocks = {}
        text = src.read_text()
        for el in lxml.html.fragments_fromstring(text) if text.strip() else []:
            if isinstance(el, str) or not el.get("data-b"):
                continue
            el.set("data-src", slug)
            blocks[int(el.get("data-b"))] = lxml.html.tostring(el, encoding="unicode", with_tail=False)
        cache[slug] = blocks
    return cache[slug]


def expand_sources(chapter_html: str, items_dir: Path, _cache: dict | None = None) -> str:
    cache = {} if _cache is None else _cache

    def place(m: re.Match) -> str:
        attrs = dict(ATTR.findall(m.group(1)))
        slug = attrs.get("item", "")
        if "b" in attrs:
            a = b = int(attrs["b"])
        else:
            a, b = int(attrs.get("from", 0)), int(attrs.get("to", 0))
        blocks = _blocks(slug, items_dir, cache)
        if not (1 <= a <= b and all(n in blocks for n in range(a, b + 1))):
            raise ValueError(f"x-src: {slug} blocks {a}–{b} out of range (it has 1–{len(blocks)})")
        return "".join(blocks[n] for n in range(a, b + 1))

    return X_SRC.sub(place, chapter_html)


def assemble(issue_dir: Path) -> Path:
    info = json.loads((issue_dir / "issue.json").read_text())
    month = datetime.strptime(info["month"], "%Y-%m").strftime("%B %Y")
    cache: dict = {}
    body = "\n".join(expand_sources(c.read_text(), issue_dir / "items", cache)
                     for c in sorted((issue_dir / "chapters").glob("*.html")))
    for name in ("reader.css", "reader.js"):
        shutil.copy(READER / name, issue_dir / name)
    index = issue_dir / "index.html"
    index.write_text(SKELETON.format(title=f"Issue {info['number']} · {month}", body=body))
    return index
