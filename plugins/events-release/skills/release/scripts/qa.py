"""QA gate for a release pack: limits, OCR for real/junk data in every image and video frame, text lint on the note.

    python3 -I qa.py <RUN> [--note-only] [--no-ocr]

Writes RUN/qa/report.md and exits 1 if there is any ERROR (warnings never block).
Author-approved exceptions: one string per line in RUN/qa/allow.txt (exact text, case-insensitive).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

KIT = Path(__file__).resolve().parents[1]
MAX_IMAGES = 9
CARD_SIZE = (3200, 2000)
MAX_VIDEO_MB = 100
VIDEO_SECONDS = (30, 120)
FRAME_EVERY = 2.0  # seconds between sampled video frames

# Staging junk and placeholders: never in a public image.
JUNK = re.compile(r"\b(test(ing)?|temp|dummy|sample|asdf|qwerty|lorem|ipsum|untitled|sachin|xyz)\b|t{4,}|\(copy\)|\bcopy of\b", re.I)
# Real-world names that leaked into past shots (guardrails); extend when a new one is caught.
REAL = re.compile(r"\b(levelup|boostability|helped\.com|project blue|hilton|anatole|gokollab)\b", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
OK_EMAIL = re.compile(r"@(example\.com|northstarcollective\.example)$", re.I)
NAME_LIKE = re.compile(r"\b([A-Z][a-z]{2,})\s([A-Z][a-z]{2,})\b")
# Words that make a capitalised pair a UI label, not a person or brand ("Mobile App", "Media Storage").
UI_WORDS = set("""app apps client portal media storage marketplace mobile memberships membership agency payments payment
weekly updates update sale convention center centre events event summit collective settings details tickets ticket
content pages design registrations registration check overview sections section speakers speaker exhibitors exhibitor
sponsors sponsor attendees attendee agenda schedule home dashboard conversations calendars contacts opportunities
marketing automation sites reputation reporting launchpad search courses communities credentials preview published
custom notification notifications general admission business operations shared files appointments affiliates loyalty
invoices estimates contracts discover live upcoming past main ballroom studio expo hall keynote breakout workshop
panel lunch learn rooftop terrace platinum gold silver booth lead leads connect connections chat profile wallet add
calendar view open edit save cancel make customize mobile web store google play your get started access""".split())
MIN_CONF = 0.6
MIN_HEIGHT = 0.012  # of image height; smaller text is too blurry to OCR reliably for name checks

# Text lint for Slack copy
HTML = re.compile(r"</?[a-z][^>\n]*>|/p>|&(amp|lt|gt|nbsp|quot);", re.I)
PLACEHOLDER = re.compile(r"\{\{.*?\}\}|<[A-Z][^>\n]{0,40}>|\bTODO\b|\bTBD\b|\blorem\b|XXX", re.I)
MARKDOWN = re.compile(r"\*\*[^*\n]+\*\*|^#{1,6}\s", re.M)
REQUIRED = ["Owner:", "Team:", "Product:", "Clickup Link:", "Release Type:", "Label:", "Overview:", ":sparkles: What's New?",
            "Why", ":heart: Special Thanks", "CC :", "i18n ready?:", "Change log Link:", "Support Doc:", "Public API :",
            "Did it go through design review?:", "Designer name :"]
TYPES = ["T1 - New Product", "T2 - New Feature", "T3 - Enhancements", "T4 - Internal Release / Bug Fixes"]
LABELS = ["Announce", "Do not Announce", "LevelUp Release - Do not Announce"]


@dataclass
class Finding:
    level: str  # ERROR | WARN
    where: str
    what: str


def world_names() -> set[str]:
    w = json.loads((KIT / "northstar" / "world.json").read_text())
    names = {p["name"] for p in w["speakers"]} | {e["name"] for e in w["exhibitors"]} | {w["staging"]["persona"]["name"]}
    names |= set(w["attendees"]["vip"]) | set(w["attendees"]["general"])
    names |= {w["brand"]["organization"], w["event"]["name"], w["event"].get("venue_name", "")} | {p["company"] for p in w["speakers"]}
    names |= {row["from"] for row in w.get("inbox", [])}
    names |= {sess["title"] for sess in w.get("sessions", [])}  # titles contain capitalised pairs ("Burning Out")
    return {n.lower() for n in names}


def allowed(run: Path) -> set[str]:
    f = run / "qa" / "allow.txt"
    return {line.strip().lower() for line in f.read_text().splitlines() if line.strip()} if f.is_file() else set()


def ocr(files: list[Path]) -> dict[str, list[tuple[str, float, float]]]:
    """Text lines per file as (text, confidence, height as a fraction of the image)."""
    if not files:
        return {}
    res = subprocess.run(["swift", str(KIT / "scripts" / "ocr.swift"), *map(str, files)], capture_output=True, text=True, timeout=900)
    if res.returncode != 0:
        raise RuntimeError(f"OCR failed: {res.stderr.strip()[-300:]}")
    out = {}
    for line in res.stdout.splitlines():
        if line.startswith("{"):
            d = json.loads(line)
            out[d["file"]] = [(ln["text"], ln["conf"], ln["box"][3]) for ln in d["lines"] if ln["conf"] >= 0.3]
    return out


def check_text_seen(where: str, lines: list[tuple[str, float, float]], names: set[str], allow: set[str]) -> list[Finding]:
    """Rules for text visible in an image or video frame."""
    found: list[Finding] = []
    for text, conf, height in lines:
        low = text.lower()
        if any(a in low for a in allow):
            continue
        if JUNK.search(text):
            found.append(Finding("ERROR", where, f"staging junk / placeholder text: {text!r}"))
        if HTML.search(text) or re.search(r"\w/p>?$", text):
            found.append(Finding("ERROR", where, f"stray HTML in the image: {text!r}"))
        if REAL.search(text):
            found.append(Finding("ERROR", where, f"real-world name: {text!r}"))
        for m in EMAIL.finditer(text):
            if not OK_EMAIL.search(m.group(0)):
                found.append(Finding("ERROR", where, f"non-fictional email: {m.group(0)!r}"))
        if conf < MIN_CONF or height < MIN_HEIGHT:
            continue
        for m in NAME_LIKE.finditer(text):
            pair = m.group(0).lower()
            if m.group(1).lower() in UI_WORDS or m.group(2).lower() in UI_WORDS:
                continue
            if pair not in names and not any(pair in n or n in pair for n in names):
                found.append(Finding("WARN", where, f"name-like text not in the Northstar world (check it): {m.group(0)!r}"))
    return found


def lint_copy(where: str, text: str, allow: set[str], markdown_ok: bool = False) -> list[Finding]:
    """Rules for Slack copy (note, review post, subtitles)."""
    found: list[Finding] = []
    for i, line in enumerate(text.splitlines(), 1):
        if any(a in line.lower() for a in allow):
            continue
        loc = f"{where}:{i}"
        if HTML.search(line):
            found.append(Finding("ERROR", loc, f"stray HTML: {line.strip()[:80]!r}"))
        if PLACEHOLDER.search(line):
            found.append(Finding("ERROR", loc, f"unfilled placeholder: {line.strip()[:80]!r}"))
        # the team format itself has double spaces around the :gohighlevel: headline and after "CC :"
        if re.search(r"\S {2,}\S", line) and ":gohighlevel:" not in line and not line.startswith("CC :"):
            found.append(Finding("ERROR", loc, f"double space: {line.strip()[:80]!r}"))
        if line.rstrip() != line and line.strip() and not re.match(r"^(Team|Release Type|Label):\s*$", line):
            found.append(Finding("WARN", loc, "trailing whitespace"))
    if not markdown_ok and MARKDOWN.search(text):
        found.append(Finding("ERROR", where, "markdown Slack won't render (**bold** or # heading); use *bold* / plain lines"))
    return found


def lint_note(where: str, text: str) -> list[Finding]:
    found = [Finding("ERROR", where, f"missing section: {s!r}") for s in REQUIRED if s not in text]
    if text.count(":gohighlevel:") < 2:
        found.append(Finding("ERROR", where, "headline line must be wrapped in :gohighlevel: ... :gohighlevel:"))
    if not any(t in text for t in TYPES):
        found.append(Finding("ERROR", where, f"Release Type must be one of {TYPES}"))
    if not any(re.search(rf"^{re.escape(lb)}\s*$", text, re.M) for lb in LABELS):
        found.append(Finding("ERROR", where, f"Label must be one of {LABELS}"))
    if "Northstar" in text:
        found.append(Finding("ERROR", where, "Northstar is screenshot data only; it must not appear in the note text"))
    found += lint_whats_new(where, text)
    return found


def lint_whats_new(where: str, text: str) -> list[Finding]:
    """2–9 sub-features, each opened by its own emoji line, no emoji used twice."""
    start = text.find(":sparkles: What's New?")
    end = text.find(":bulb:", start)
    if start < 0 or end < 0:
        return []
    heads = re.findall(r"^(:[a-z0-9_+-]+:)\s+\S", text[start + 22:end], re.M)
    found: list[Finding] = []
    if not 2 <= len(heads) <= 9:
        found.append(Finding("ERROR", where, f"What's New has {len(heads)} sub-features; the team format uses 2–9"))
    dupes = sorted({h for h in heads if heads.count(h) > 1})
    if dupes:
        found.append(Finding("ERROR", where, f"emoji used for more than one sub-feature: {', '.join(dupes)}"))
    return found


def lint_mentions(note: str, mentions_file: Path) -> list[Finding]:
    """Every @mention in the note must be in mentions.txt, or the post step can't turn it into a real mention."""
    if not mentions_file.is_file():
        return [Finding("ERROR", "note/mentions.txt", "missing (the post step needs it)")]
    listed = {line.strip().lstrip("@").lower() for line in mentions_file.read_text().splitlines() if line.strip()}
    found: list[Finding] = []
    for m in sorted(set(re.findall(r"@([\w-]+(?: [A-Z][\w-]*)*(?: \(High[Ll]evel\))?)", note))):
        key = m.lower()
        if not any(key == x or key.startswith(x) or x.startswith(key) for x in listed):
            found.append(Finding("ERROR", "note/mentions.txt", f"@{m} is mentioned in the note but not listed"))
    return found


def video_frames(video: Path, tmp: Path) -> list[Path]:
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps=1/{FRAME_EVERY},scale=1600:-1", str(tmp / "f%04d.png")], check=True)
    return sorted(tmp.glob("f*.png"))


def video_info(video: Path) -> tuple[float, float]:
    res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)], capture_output=True, text=True)
    return float(res.stdout.strip() or 0), video.stat().st_size / 1e6


def run_qa(run: Path, note_only: bool = False, use_ocr: bool = True) -> list[Finding]:
    status = json.loads((run / "status.json").read_text())
    allow = allowed(run)
    found: list[Finding] = []

    note_dir = run / "note"
    for name in ("release-note.md", "review-post.md", "form-handoff.md"):
        f = note_dir / name
        if not f.is_file():
            found.append(Finding("ERROR", f"note/{name}", "missing"))
            continue
        text = f.read_text()
        found += lint_copy(f"note/{name}", text, allow, markdown_ok=name == "form-handoff.md")
        if name in ("release-note.md", "review-post.md"):
            found += lint_note(f"note/{name}", text)
        if name == "review-post.md":
            found += lint_mentions(text, note_dir / "mentions.txt")
            first = text.splitlines()[0] if text.strip() else ""
            if not first.startswith(":eyes:"):
                found.append(Finding("ERROR", "note/review-post.md:1", "first line must be the :eyes: review line"))
    if note_only:
        return found

    images = sorted((run / "shots" / "final").glob("*.png"))
    if not images:
        found.append(Finding("ERROR", "shots/final", "no images"))
    if len(images) > MAX_IMAGES:
        found.append(Finding("ERROR", "shots/final", f"{len(images)} images; a post holds at most {MAX_IMAGES} + 1 video"))
    for im in images:
        with Image.open(im) as img:
            if img.size != CARD_SIZE:
                found.append(Finding("ERROR", f"shots/final/{im.name}", f"size {img.size}, cards are {CARD_SIZE}"))

    video = run / "video" / "video.mp4"
    frames: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        if status.get("video") == "yes":
            if not video.is_file():
                found.append(Finding("ERROR", "video/video.mp4", "missing (video = yes)"))
            else:
                secs, mb = video_info(video)
                if mb >= MAX_VIDEO_MB:
                    found.append(Finding("ERROR", "video/video.mp4", f"{mb:.1f} MB; must be under {MAX_VIDEO_MB} MB"))
                if not VIDEO_SECONDS[0] <= secs <= VIDEO_SECONDS[1]:
                    found.append(Finding("WARN", "video/video.mp4", f"{secs:.0f}s; house length is {VIDEO_SECONDS[0]}–{VIDEO_SECONDS[1]}s"))
                if use_ocr:
                    frames = video_frames(video, Path(tmp))
            manifest = run / "video" / "vo" / "vo-manifest.json"
            if manifest.is_file():
                subs = "\n".join(line["text"] for line in json.loads(manifest.read_text()))
                found += lint_copy("video subtitles", subs, allow)
        if use_ocr:
            names = world_names()
            seen = ocr(images + frames)
            for path, lines in seen.items():
                p = Path(path)
                where = f"video @ {(int(p.stem[1:]) - 1) * FRAME_EVERY:.0f}s" if p in frames else f"shots/final/{p.name}"
                found += check_text_seen(where, lines, names, allow)
    return found


def report(run: Path, found: list[Finding], name: str = "report.md") -> Path:
    errors = [f for f in found if f.level == "ERROR"]
    warns = [f for f in found if f.level == "WARN"]
    # collapse repeated warnings (the same name on many frames)
    seen: dict[str, Finding] = {}
    for w in warns:
        seen.setdefault(w.what, w)
    lines = [f"# QA report: {'FAIL' if errors else 'PASS'} ({len(errors)} errors, {len(seen)} warnings)", ""]
    lines += [f"- ERROR {f.where}: {f.what}" for f in errors]
    lines += [f"- WARN {f.where}: {f.what}" for f in seen.values()]
    lines += ["", "Approved exceptions go in qa/allow.txt (one exact string per line)."]
    out = run / "qa" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    run = Path(argv[1])
    try:
        found = run_qa(run, note_only="--note-only" in argv, use_ocr="--no-ocr" not in argv)
    except (OSError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as err:
        print(f"qa.py: {err}", file=sys.stderr)
        return 1
    path = report(run, found, "report-note.md" if "--note-only" in argv else "report.md")
    print(path.read_text())
    return 1 if any(f.level == "ERROR" for f in found) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
