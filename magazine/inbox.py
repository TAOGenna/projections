"""The inbox: one markdown file of links, parsed into entries, archived into an issue once used."""
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

BULLET = re.compile(r"^[-*]\s+")
CHECKBOX = re.compile(r"^\[[ xX]\]\s+")
MD_LINK = re.compile(r"^\[([^\]]*)\]\(((?:[^\s()]|\([^\s()]*\))+)\)")  # one level of (…) inside the URL
SEPARATORS = (" — ", " -- ", " - ")


@dataclass(frozen=True)
class Entry:
    url: str
    note: str = ""


def _entry(line: str) -> Entry | None:
    s = CHECKBOX.sub("", BULLET.sub("", line.strip()))
    if m := MD_LINK.match(s):
        return Entry(_clean(m.group(2)), m.group(1).strip())
    if not s.startswith(("http://", "https://", "<http", "file://")):
        return None
    cuts = [(s.find(sep), sep) for sep in SEPARATORS if sep in s]
    if cuts:
        i, sep = min(cuts)
        head, note = s[:i], s[i + len(sep):].strip()
    else:
        head, note = s, ""
    return Entry(_clean(head.split()[0]), note)


def _clean(url: str) -> str:
    """Drop <> and trailing punctuation; a closing parenthesis only when it has no opening one."""
    url = url.strip().lstrip("<")
    while url and (url[-1] in ".,;>" or (url[-1] == ")" and url.count(")") > url.count("("))):
        url = url[:-1]
    return url


def parse_inbox(text: str) -> list[Entry]:
    seen, out = set(), []
    for line in text.splitlines():
        e = _entry(line)
        if e and e.url not in seen:
            seen.add(e.url)
            out.append(e)
    return out


def slug_for(url: str, taken: set[str]) -> str:
    u = urlparse(url)
    host = u.hostname or ""
    host = host.removeprefix("www.").rsplit(".", 1)[0]
    parts = [p for p in u.path.split("/") if p][-3:]
    if u.scheme == "file":  # a note on disk is named by its file, not its folders
        host, parts = "", [unquote(parts[-1]).rsplit(".", 1)[0]] if parts else []
    slug = re.sub(r"[^a-z0-9]+", "-", "-".join([host, *parts]).lower()).strip("-")[:48].strip("-") or "item"
    if slug not in taken:
        return slug
    n = 2
    while f"{slug}-{n}" in taken:
        n += 1
    return f"{slug}-{n}"


def archive(inbox: Path, issue_dir: Path, used: list[Entry]) -> None:
    urls = {e.url for e in used}
    issue_dir.mkdir(parents=True, exist_ok=True)
    with (issue_dir / "inbox.md").open("a") as f:
        for e in used:
            f.write(f"- {e.url} — {e.note}\n" if e.note else f"- {e.url}\n")
    keep = [line for line in inbox.read_text().splitlines(keepends=True)
            if not ((e := _entry(line)) and e.url in urls)]
    inbox.write_text("".join(keep))
