"""`python -m magazine open`: coming back to an issue is one command."""
import pytest

from magazine import __main__ as cli


@pytest.fixture
def issues(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "ISSUES", tmp_path)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    opened = []
    monkeypatch.setattr("webbrowser.open", opened.append)
    return tmp_path, opened


def test_open_opens_the_latest_issue_or_a_given_month(issues):
    root, opened = issues
    for month in ("2026-10", "2026-11"):
        (root / month).mkdir()
        (root / month / "index.html").write_text("<html></html>")
    cli.main(["open"])
    assert opened == [(root / "2026-11" / "index.html").as_uri()]
    cli.main(["open", "2026-10"])
    assert opened[-1] == (root / "2026-10" / "index.html").as_uri()


def test_open_says_when_the_issue_is_not_built_yet(issues):
    root, opened = issues
    (root / "2026-11").mkdir()
    with pytest.raises(SystemExit, match="assemble"):
        cli.main(["open"])
    assert opened == []
