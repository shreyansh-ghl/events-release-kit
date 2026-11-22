"""Behaviour tests for the QA gate (note lint, limits, OCR rules)."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import qa  # noqa: E402
import run as runlib  # noqa: E402

KIT = Path(__file__).resolve().parents[1]
GOOD_NOTE = """-----
           :gohighlevel: Introducing Events' Coupon Codes: Fill More Seats  :gohighlevel:
-----

Owner: @Jordan Blake (HighLevel)
Team: 
Revex
Product: Events
Clickup Link: https://app.clickup.com/t/8631005/abc
-----

Release Type: 
T2 - New Feature

Label: 
Announce

Overview:
Discounts used to mean manual refunds. Now organizers create coupon codes in Events.

:sparkles: What's New?

:admission_tickets: Coupon Codes at Checkout
Attendees apply a code and see the new total before paying.

:date: Codes With an End Date
Set when each code expires.

:bulb: Why This Matters
• For organizers: fill more seats without manual refunds.

:rocket: How to Get Started
1. Go to Events → select an event → Tickets → "Coupons".

Fill more seats, with less work.

:heart: Special Thanks & Shoutouts
@Sayeed (HighLevel) for guidance.

CC :  @svr- @memberships-team

i18n ready?: Yes

:paperclip: Change log Link: NA
:books: Support Doc: NA
:link: Public API : NA

Did it go through design review?: No

Designer name :NA
"""


@pytest.fixture()
def run_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("EVENTS_RELEASE_RUNS", str(tmp_path))
    d = runlib.new("coupon-codes", "Coupon codes", "Jordan")
    runlib.set_fields(d, ["video=no"])
    (d / "note" / "release-note.md").write_text(GOOD_NOTE)
    (d / "note" / "review-post.md").write_text(":eyes: Release note for review: Coupon codes.\n\n" + GOOD_NOTE)
    (d / "note" / "form-handoff.md").write_text("# Form handoff\n")
    (d / "note" / "mentions.txt").write_text("Jordan Blake (HighLevel)\nSayeed (HighLevel)\nsvr-\nmemberships-team\n")
    shutil.copy(KIT / "cards" / "tests" / "repro" / "out-02.png", d / "shots" / "final" / "01-hero.png")
    return d


def errors(found: list[qa.Finding]) -> list[str]:
    return [f"{f.where}: {f.what}" for f in found if f.level == "ERROR"]


def test_clean_pack_passes(run_dir: Path) -> None:
    assert errors(qa.run_qa(run_dir)) == []


@pytest.mark.parametrize("bad, expect", [
    ("Members manage tickets in the portal they already use./p>", "stray HTML"),
    ("Members  manage tickets.", "double space"),
    ("Owner: {{author}}", "placeholder"),
    ("**Coupon codes** are here", "markdown"),
    ("Seen at Northstar Summit.", "Northstar"),
])
def test_note_copy_errors(run_dir: Path, bad: str, expect: str) -> None:
    f = run_dir / "note" / "release-note.md"
    f.write_text(f.read_text().replace("Discounts used to mean manual refunds.", bad))
    assert any(expect in e for e in errors(qa.run_qa(run_dir, note_only=True)))


def test_missing_section_and_bad_label(run_dir: Path) -> None:
    f = run_dir / "note" / "review-post.md"
    f.write_text(f.read_text().replace("Designer name :NA", "").replace("\nAnnounce\n", "\nShip it\n"))
    errs = errors(qa.run_qa(run_dir, note_only=True))
    assert any("Designer name" in e for e in errs) and any("Label must be" in e for e in errs)


def test_too_many_images_and_wrong_size(run_dir: Path) -> None:
    for i in range(9):
        Image.new("RGB", (3200, 2000), "white").save(run_dir / "shots" / "final" / f"0{i + 2}.png")
    Image.new("RGB", (1600, 1000), "white").save(run_dir / "shots" / "final" / "99-small.png")
    errs = errors(qa.run_qa(run_dir, use_ocr=False))
    assert any("at most 9" in e for e in errs) and any("99-small" in e for e in errs)


def test_missing_video_when_video_is_yes(run_dir: Path) -> None:
    runlib.set_fields(run_dir, ["video=yes"])
    assert any("video.mp4" in e for e in errors(qa.run_qa(run_dir, use_ocr=False)))


def test_ocr_flags_junk_real_email_and_allow_list(run_dir: Path) -> None:
    img = Image.new("RGB", (3200, 2000), "white")
    font = ImageFont.truetype(str(KIT / "fonts" / "Inter-Variable.ttf"), 90)
    d = ImageDraw.Draw(img)
    d.text((200, 300), "Test Internal Event", fill="black", font=font)
    d.text((200, 600), "contact: jane@acme.com", fill="black", font=font)
    img.save(run_dir / "shots" / "final" / "02-bad.png")
    errs = errors(qa.run_qa(run_dir))
    assert any("staging junk" in e and "02-bad" in e for e in errs)
    assert any("non-fictional email" in e for e in errs)
    (run_dir / "qa" / "allow.txt").write_text("Test Internal Event\njane@acme.com\n")
    assert errors(qa.run_qa(run_dir)) == []


def test_report_marks_fail(run_dir: Path) -> None:
    out = qa.report(run_dir, [qa.Finding("ERROR", "x", "y"), qa.Finding("WARN", "a", "b"), qa.Finding("WARN", "c", "b")])
    text = out.read_text()
    assert text.startswith("# QA report: FAIL (1 errors, 1 warnings)")


def test_ocr_catches_stray_html_in_reference_card(run_dir: Path) -> None:
    shutil.copy(KIT / "tests" / "fixtures" / "02-events-in-client-portal.png", run_dir / "shots" / "final" / "02-ref.png")
    assert any("stray HTML" in e and "02-ref" in e for e in errors(qa.run_qa(run_dir)))


def test_whats_new_count_and_duplicate_emoji(run_dir: Path) -> None:
    f = run_dir / "note" / "release-note.md"
    f.write_text(f.read_text().replace(":date: Codes With an End Date", ":admission_tickets: Codes With an End Date"))
    assert any("more than one sub-feature" in e for e in errors(qa.run_qa(run_dir, note_only=True)))
    f.write_text(GOOD_NOTE.replace(":date: Codes With an End Date\nSet when each code expires.\n", ""))
    assert any("sub-features" in e for e in errors(qa.run_qa(run_dir, note_only=True)))


def test_unlisted_mention_and_missing_review_line(run_dir: Path) -> None:
    f = run_dir / "note" / "review-post.md"
    f.write_text(GOOD_NOTE.replace("@Sayeed (HighLevel) for guidance.", "@Vooha (HighLevel) for testing."))
    errs = errors(qa.run_qa(run_dir, note_only=True))
    assert any("@Vooha (HighLevel) is mentioned" in e for e in errs)
    assert any(":eyes:" in e for e in errs)


def test_note_only_writes_its_own_report(run_dir: Path) -> None:
    assert qa.main(["qa.py", str(run_dir), "--note-only"]) == 0
    assert (run_dir / "qa" / "report-note.md").is_file() and not (run_dir / "qa" / "report.md").exists()
