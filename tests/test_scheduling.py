"""Weekly publishing (2026-10-28): approved posts go live on their Tuesday at 8am Eastern through a GitHub Action, and
scheduled posts waiting in content/ are kept off the live site."""

from conftest import ROOT

WORKFLOW = ROOT / ".github" / "workflows" / "publish-scheduled-posts.yml"


def test_the_workflow_runs_on_tuesday_mornings_in_both_clock_settings():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '- cron: "0 12 * * 2"' in text and '- cron: "0 13 * * 2"' in text  # 8am EDT and 8am EST
    assert "workflow_dispatch" in text


def test_the_workflow_tests_before_it_pushes_and_only_when_something_is_due():
    text = WORKFLOW.read_text(encoding="utf-8")
    build, test, publish = (text.index(s) for s in ("python build.py", "python -m pytest", "git push"))
    assert build < test < publish
    assert text.count("steps.build.outputs.changed == 'true'") >= 2


def test_content_is_not_served():
    fn = (ROOT / "functions" / "content" / "[[path]].js").read_text(encoding="utf-8")
    assert "export function onRequest" in fn and "status: 404" in fn


def test_the_sitemap_submission_is_skipped_without_a_key(monkeypatch, capsys):
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    import submit_sitemap
    monkeypatch.delenv("GSC_SERVICE_ACCOUNT_JSON", raising=False)
    assert submit_sitemap.main() == 0
    assert "skipping" in capsys.readouterr().out
    assert submit_sitemap.submit_url("sc-domain:ayinadvisors.com") == (
        "https://www.googleapis.com/webmasters/v3/sites/sc-domain%3Aayinadvisors.com"
        "/sitemaps/https%3A%2F%2Fayinadvisors.com%2Fsitemap.xml")
