"""Behaviour tests for the ClickUp/PR condenser."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import facts  # noqa: E402

TASK = {"result": {"name": "Coupon codes", "url": "https://app.clickup.com/t/abc", "status": {"status": "closed"},
                   "list": {"name": "Roadmap"}, "assignees": [{"username": "Jordan Blake"}], "tags": [{"name": "events"}],
                   "checklists": [{"name": "QA", "items": [{"name": "Apply code"}, {"name": "Expiry"}]}],
                   "text_content": "x" * 5000, "custom_fields": [{"id": str(i)} for i in range(54)]}}


def test_clickup_keeps_release_facts_and_trims(tmp_path: Path) -> None:
    f = tmp_path / "saved.txt"
    f.write_text("Output saved:\n" + json.dumps(TASK))
    md = facts.clickup_md(facts.load_task(f))
    assert "### ClickUp: Coupon codes" in md and "Jordan Blake" in md and "Apply code; Expiry" in md
    assert "(trimmed)" in md and len(md) < facts.MAX_TEXT + 600
    assert "custom_fields" not in md


def test_bot_reviewers_are_not_thanked() -> None:
    for bot in ("orca-security-us", "sentry-io[bot]", "github-actions", "coderabbitai", "renovatebot"):
        assert facts.BOTS.search(bot), bot
    for person in ("sayeed38", "shreyansh-ghl", "talbot"):
        assert not facts.BOTS.search(person), person
