"""Behaviour tests for the card renderer: spec lint/validation and a real render of each layout."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render_card  # noqa: E402

REPRO = Path(__file__).resolve().parent / "repro"


def write_spec(tmp_path: Path, **overrides: object) -> Path:
    spec = json.loads((REPRO / "02.json").read_text())
    spec["frame"]["src"] = str(REPRO / "in-02-portal.png")
    spec.update(overrides)
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    return path


@pytest.mark.parametrize("subhead", [
    "Members manage tickets in the portal they already use./p>",
    "Members manage <b>tickets</b>.",
    "Members  manage tickets.",
    "Members manage tickets..",
    "TODO write subhead",
])
def test_rejects_broken_copy(tmp_path: Path, subhead: str) -> None:
    with pytest.raises(render_card.SpecError):
        render_card.render(write_spec(tmp_path, subhead=subhead), tmp_path / "out.png")


@pytest.mark.parametrize("headline", ["No italic word here.", "*Two* italic *words*.", "Unbalanced *star."])
def test_headline_needs_exactly_one_italic_phrase(tmp_path: Path, headline: str) -> None:
    with pytest.raises(render_card.SpecError, match="headline"):
        render_card.render(write_spec(tmp_path, headline=headline), tmp_path / "out.png")


def test_rejects_missing_image(tmp_path: Path) -> None:
    with pytest.raises(render_card.SpecError, match="image not found"):
        render_card.render(write_spec(tmp_path, frame={"src": "nope.png"}), tmp_path / "out.png")


def test_lowercase_kicker_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(render_card.SpecError, match="kicker"):
        render_card.render(write_spec(tmp_path, kicker="New in HighLevel Events"), tmp_path / "out.png")


@pytest.mark.parametrize("spec_name", ["02.json", "04.json", "layers.json"])
def test_renders_3200x2000_png(tmp_path: Path, spec_name: str) -> None:
    out = render_card.render(REPRO / spec_name, tmp_path / "card.png")
    with Image.open(out) as im:
        assert im.size == (3200, 2000)
        # paper background, not a blank or black page
        r, g, b = im.convert("RGB").getpixel((10, 10))
        assert 215 < r < 245 and abs(r - b) < 16


def test_overlong_side_headline_fails_render(tmp_path: Path) -> None:
    spec = json.loads((REPRO / "04.json").read_text())
    for ph in spec["phones"]:
        ph["src"] = str(REPRO / ph["src"])
    spec["headline"] = "A much longer headline that will *never* fit on two lines of the card."
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    with pytest.raises(RuntimeError, match="3\\+ lines"):
        render_card.render(path, tmp_path / "out.png")
