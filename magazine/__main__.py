"""python -m magazine start | recapture | assemble | bake | check | open | archive"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

from magazine.inbox import Entry, archive

ROOT = Path(__file__).resolve().parent.parent
ISSUES = ROOT / "issues"
INBOX = ROOT / "inbox.md"


def issue_dir(month: str | None) -> Path:
    if month:
        return ISSUES / month
    folders = sorted(p for p in ISSUES.glob("*") if p.is_dir()) if ISSUES.exists() else []
    if not folders:
        sys.exit("no issues yet: run `python -m magazine start` first")
    return folders[-1]


def cmd_archive(args) -> None:
    d = issue_dir(args.month)
    used = []
    for meta in sorted(d.glob("items/*/meta.json")):
        m = json.loads(meta.read_text())
        # the inbox holds the link as saved, which differs from `url` when a front page was resolved
        used.append(Entry(m.get("saved_url") or m["url"], m.get("note", "")))
    archive(INBOX, d, used)
    print(f"archived {len(used)} entries into {d.relative_to(ROOT)}/inbox.md")


def cmd_start(args) -> None:
    from magazine.capture import capture_all
    from magazine.inbox import parse_inbox
    metas = capture_all(parse_inbox(INBOX.read_text()), ISSUES / args.month, force=args.force)
    for m in metas:
        print(f"{m.get('slug', '?')}  {m.get('kind', '?')}  {m.get('status', '?')}  {m.get('blocks', 0)}  {m.get('reason', '')}")


def cmd_recapture(args) -> None:
    from magazine.capture import recapture
    m = recapture(issue_dir(args.month), args.slug, args.url)
    print(f"{m['slug']}  {m['kind']}  {m['status']}  {m['blocks']}  {m['reason']}  (saved as {m['saved_url']})")


def cmd_assemble(args) -> None:
    from magazine.assemble import assemble
    index = assemble(issue_dir(args.month))
    print(f"wrote {index.relative_to(ROOT)}")


def cmd_bake(args) -> None:
    from magazine.bake import bake
    print(f"baked {bake(issue_dir(args.month))} heavy layers into images")


def cmd_check(args) -> None:
    from magazine.check import check
    problems = check(issue_dir(args.month), shots=args.shots)
    print("\n".join(problems) or "ok")
    if problems:
        sys.exit(1)


def cmd_open(args) -> None:
    """Opens an issue in the browser, the latest unless a month is given; the reader resumes where you left off."""
    import webbrowser
    index = issue_dir(args.month) / "index.html"
    if not index.exists():
        sys.exit(f"{index.relative_to(ROOT)} isn't built yet: run `python -m magazine assemble` first")
    webbrowser.open(index.as_uri())
    print(f"opened {index.relative_to(ROOT)}")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="magazine")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start", help="capture every inbox link into issues/<month>/items/")
    s.add_argument("--month", default=date.today().strftime("%Y-%m"))
    s.add_argument("--force", action="store_true", help="capture again even if already captured")
    s = sub.add_parser("recapture", help="capture URL into an item's folder in place of the link as saved")
    s.add_argument("slug")
    s.add_argument("url")
    s.add_argument("--month", default=None, help="YYYY-MM (default: the latest issue)")
    for name in ("assemble", "bake", "check", "open", "archive"):
        s = sub.add_parser(name)
        s.add_argument("month", nargs="?", help="YYYY-MM (default: the latest issue)")
        if name == "check":
            s.add_argument("--shots", action="store_true", help="also save proofs/NN.png per spread")
    args = p.parse_args(argv)
    commands = {"start": cmd_start, "recapture": cmd_recapture, "assemble": cmd_assemble, "bake": cmd_bake, "check": cmd_check,
                "open": cmd_open, "archive": cmd_archive}
    if args.cmd not in commands:
        sys.exit(f"`{args.cmd}` is not built yet")
    commands[args.cmd](args)


if __name__ == "__main__":
    main()
