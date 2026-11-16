from magazine.inbox import Entry, archive, parse_inbox, slug_for


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


def test_urls_with_parentheses_survive():
    text = """- https://en.wikipedia.org/wiki/Winding_number_(complex_analysis)
* [wn](https://en.wikipedia.org/wiki/Euler_(disambiguation))
- https://c.com/z).
"""
    assert [e.url for e in parse_inbox(text)] == ["https://en.wikipedia.org/wiki/Winding_number_(complex_analysis)",
                                                 "https://en.wikipedia.org/wiki/Euler_(disambiguation)",
                                                 "https://c.com/z"]
