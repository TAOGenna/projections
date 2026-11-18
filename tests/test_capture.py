import json

import magazine.capture as capture_mod
from magazine.capture import capture_all, kind_of, looks_blocked, recapture
from magazine.inbox import Entry


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
    # a long article that mentions "access denied" is an article
    assert not looks_blocked("On permissions", "When the server says access denied, " + "word " * 800)


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


def test_recapture_keeps_saved_url(tmp_path, monkeypatch):
    # the inbox saved a blog's front page; its note names one post, which is what gets captured
    d = tmp_path / "items" / "andrewkchan"; d.mkdir(parents=True)
    (d / "meta.json").write_text('{"url": "https://andrewkchan.dev/", "note": "crawling a billion pages"}')
    (d / "stale.png").write_text("x")
    monkeypatch.setattr(capture_mod, "capture",
        lambda e, d, b: (d.mkdir(parents=True, exist_ok=True), {"url": e.url, "note": e.note})[1])
    meta = recapture(tmp_path, "andrewkchan", "https://andrewkchan.dev/posts/crawler.html")
    assert meta["url"] == "https://andrewkchan.dev/posts/crawler.html" and meta["saved_url"] == "https://andrewkchan.dev/"
    assert json.loads((d / "meta.json").read_text())["saved_url"] == "https://andrewkchan.dev/"
    assert not (d / "stale.png").exists()


def _fake_capture(calls):
    def fake(e, d, b):
        calls.append(e.url)
        d.mkdir(parents=True, exist_ok=True)
        meta = {"url": e.url, "note": e.note, "slug": d.name, "status": "ok"}
        (d / "meta.json").write_text(json.dumps(meta))
        return meta
    return fake


def test_capture_all_retries_unreadable_items(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(capture_mod, "capture", _fake_capture(calls))
    d = tmp_path / "items" / "a-one"; d.mkdir(parents=True)
    (d / "meta.json").write_text('{"url": "https://a.com/one", "status": "unreadable", "reason": "Timeout"}')
    capture_all([Entry("https://a.com/one")], tmp_path)
    assert calls == ["https://a.com/one"]


def test_force_recapture_keeps_a_resolved_link(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(capture_mod, "capture", _fake_capture(calls))
    d = tmp_path / "items" / "andrewkchan"; d.mkdir(parents=True)
    (d / "meta.json").write_text('{"url": "https://andrewkchan.dev/posts/crawler.html", '
                                 '"saved_url": "https://andrewkchan.dev/", "status": "ok"}')
    capture_all([Entry("https://andrewkchan.dev/", "crawling")], tmp_path, force=True)
    assert calls == ["https://andrewkchan.dev/posts/crawler.html"]
    assert json.loads((d / "meta.json").read_text())["saved_url"] == "https://andrewkchan.dev/"


def test_capture_all_never_reuses_another_links_folder(tmp_path, monkeypatch):
    # two YouTube links share a slug base; a link added above the other must not inherit its folder
    calls = []
    monkeypatch.setattr(capture_mod, "capture", _fake_capture(calls))
    d = tmp_path / "items" / "youtube-watch"; d.mkdir(parents=True)
    (d / "meta.json").write_text('{"url": "https://www.youtube.com/watch?v=A", "status": "ok"}')
    capture_all([Entry("https://www.youtube.com/watch?v=B"), Entry("https://www.youtube.com/watch?v=A")], tmp_path)
    assert calls == ["https://www.youtube.com/watch?v=B"]
    assert json.loads((tmp_path / "items" / "youtube-watch" / "meta.json").read_text())["url"].endswith("v=A")


def test_markdown_note_title_math_callouts_lists():
    from magazine.capture import kind_of, markdown_fragment
    assert kind_of("file:///a/b.md") == "markdown" and kind_of("https://x.org/notes.md") == "markdown"
    title, body, maths = markdown_fragment(
        "# The title\n\nCosts $5 and $6, see [[Other note|that note]]; $\\rho$cm and `$code$`.\n\n"
        "> [!important] Hinges\n> Sort them.\n> 1. one\n\n$$\na^2\n$$\n\n3. three\n4. four\n\n- [ ] todo\n- [x] done\n")
    assert title == "The title" and "The title" not in body
    assert maths == [("\\rho", False), ("a^2", True)]
    assert "Costs $5 and $6, see that note; ⟦m0⟧cm and <code>$code$</code>." in body
    assert '<blockquote class="callout" data-callout="important">' in body
    assert '<p class="callout-title">Hinges</p>' in body and "<ol>" in body  # the list inside the callout is a list
    assert '<ol start="3"><li>three</li></ol><ol start="4"><li>four</li></ol>' in body.replace("\n</ol>", "</ol>")
    assert '<li class="task">todo</li>' in body and '<li class="task done">done</li>' in body
