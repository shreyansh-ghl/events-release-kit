"""Render a house screenshot card (3200x2000 PNG) from a JSON spec with headless Chrome.

Usage:
    python3 -I render_card.py spec.json out.png
    python3 -I render_card.py spec.json out.png --html     # also keep the built HTML for debugging

Spec (paths are relative to the spec file):
  {
    "layout": "hero" | "side",
    "kicker": "NEW IN HIGHLEVEL EVENTS",       # caps, letter-spaced
    "dot": "blue" | "amber" | "green",          # hero = blue; sections cycle green, amber, blue
    "headline": "Events, now in your *Client Portal*.",   # exactly one *italic* phrase; "\n" = line break
                                                # (side cards: 2 lines max; the render fails on overflow)
    "subhead": "One or two plain sentences.",
    "bullets": ["optional", "check list"],      # side layout only
    # hero: one browser frame under the text
    "frame": {"src": "shot.png", "url": "members.northstarcollective.com/events"},
    "frame_width": 861, "frame_top": 300,
    # side: either a row of phones ...
    "stage": "phones", "phones": [{"src": "a.png", "caption": "PROFILE"}, ...],
    # ... or free layers (browser | panel | phone), CSS px on a 1600x1000 canvas
    "layers": [{"kind": "browser", "src": "x.png", "url": "...", "x": 700, "y": 120, "w": 860, "rotate": 0, "z": 1}]
  }
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "card.html"
FONTS = HERE.parent / "fonts"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
SIZE = (1600, 1000)  # CSS px; captured at device scale 2

# Text that must never reach a card (e.g. the "./p>" that slipped into the Client Portal card).
BAD_TEXT = [
    (re.compile(r"[<>]"), "contains '<' or '>' (stray HTML?)"),
    (re.compile(r"/p\b|&[a-z]+;|&#\d+;"), "contains HTML residue"),
    (re.compile(r"\s{2,}"), "contains a double space"),
    (re.compile(r"^\s|\s$"), "has leading/trailing whitespace"),
    (re.compile(r"\.\.(?!\.)|[.!?][.!?]"), "has doubled punctuation"),
    (re.compile(r"\b(lorem|ipsum|todo|tbd|xxx)\b", re.I), "contains placeholder text"),
]


class SpecError(ValueError):
    """The card spec is invalid; message says what to fix."""


def lint_text(field: str, text: str) -> list[str]:
    problems = [f"{field}: {why}" for rx, why in BAD_TEXT if rx.search(text)]
    if field == "headline":
        italics = re.findall(r"\*[^*]+\*", text)
        if text.count("*") % 2:
            problems.append("headline: unbalanced '*'")
        elif len(italics) != 1:
            problems.append(f"headline: needs exactly one *italic* phrase, found {len(italics)}")
    if field == "kicker" and text != text.upper():
        problems.append("kicker: must be upper case")
    return problems


def validate(spec: dict, base: Path) -> list[str]:
    problems: list[str] = []
    if spec.get("layout") not in ("hero", "side"):
        problems.append("layout: must be 'hero' or 'side'")
    for field in ("kicker", "headline"):
        if not isinstance(spec.get(field), str) or not spec[field]:
            problems.append(f"{field}: required")
    for field in ("kicker", "headline", "subhead"):
        if isinstance(spec.get(field), str):
            problems += lint_text(field, spec[field])
    for i, b in enumerate(spec.get("bullets") or []):
        problems += lint_text(f"bullets[{i}]", b)
    for src in image_sources(spec):
        if not (base / src).is_file():
            problems.append(f"image not found: {src}")
    if spec.get("layout") == "hero" and not (spec.get("frame") or {}).get("src"):
        problems.append("frame.src: hero needs a browser screenshot")
    if spec.get("layout") == "side" and not (spec.get("layers") or spec.get("stage") == "phones"):
        problems.append("side layout needs stage='phones' or layers")
    return problems


def image_sources(spec: dict) -> list[str]:
    items = [spec.get("frame") or {}] + list(spec.get("phones") or []) + list(spec.get("layers") or [])
    return [it["src"] for it in items if it.get("src")]


def build_html(spec: dict, base: Path) -> str:
    """Return the page with absolute file URLs and the spec embedded as JSON."""
    resolved = json.loads(json.dumps(spec))
    for group in ([resolved.get("frame")] if resolved.get("frame") else []) + \
                 list(resolved.get("phones") or []) + list(resolved.get("layers") or []):
        if group.get("src"):
            group["src"] = (base / group["src"]).resolve().as_uri()
    payload = json.dumps(resolved).replace("</", "<\\/")  # keep the JSON from closing the script tag
    html = TEMPLATE.read_text()
    return html.replace("FONTS/", FONTS.resolve().as_uri() + "/").replace("CARD_JSON", payload)


def chrome(args: list[str], profile: Path) -> subprocess.CompletedProcess:
    cmd = [str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
           "--allow-file-access-from-files", f"--user-data-dir={profile}", "--virtual-time-budget=15000",
           f"--window-size={SIZE[0]},{SIZE[1]}", "--force-device-scale-factor=2", *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def render(spec_path: Path, out_path: Path, keep_html: bool = False) -> Path:
    spec = json.loads(spec_path.read_text())
    base = spec_path.resolve().parent
    problems = validate(spec, base)
    if problems:
        raise SpecError("card spec has problems:\n  - " + "\n  - ".join(problems))
    if not CHROME.exists():
        raise FileNotFoundError(f"Google Chrome not found at {CHROME}")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        page = tmp_dir / "card.html"
        page.write_text(build_html(spec, base))
        dom = chrome(["--dump-dom", page.as_uri()], tmp_dir / "profile").stdout
        if 'data-ready="1"' not in dom:
            title = re.search(r"<title>(.*?)</title>", dom)
            raise RuntimeError(f"card page did not finish loading ({title.group(1) if title else 'no title'})")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shot = chrome([f"--screenshot={out_path.resolve()}", page.as_uri()], tmp_dir / "profile")
        if shot.returncode != 0 or not out_path.exists():
            raise RuntimeError(f"chrome screenshot failed: {shot.stderr[-500:]}")
        if keep_html:
            shutil.copy(page, out_path.with_suffix(".html"))
    return out_path


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    try:
        out = render(Path(argv[1]), Path(argv[2]), keep_html="--html" in argv)
    except (SpecError, RuntimeError, FileNotFoundError) as err:
        print(err, file=sys.stderr)
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
