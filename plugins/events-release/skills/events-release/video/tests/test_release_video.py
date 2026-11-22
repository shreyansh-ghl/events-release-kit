"""Behaviour tests for the video spec resolver and the music bed (no Remotion render needed)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bed  # noqa: E402
import release_video as rv  # noqa: E402

REPRO = Path(__file__).resolve().parents[1] / "examples" / "repro"
BASE = json.loads((REPRO / "spec.json").read_text())


def resolve(tmp_path: Path, mutate=None) -> dict:
    spec = copy.deepcopy(BASE)
    spec["vo_manifest"] = str(REPRO / "vo" / "vo-manifest.json")
    if mutate:
        mutate(spec)
    # keep image paths valid by writing the spec next to the repro assets
    path = REPRO / f"_test_{tmp_path.name}.json"
    path.write_text(json.dumps(spec))
    try:
        return rv.Resolver(path).resolve()
    finally:
        path.unlink()


def test_repro_timeline_follows_vo_lengths(tmp_path: Path) -> None:
    p = resolve(tmp_path)
    kinds = [s["kind"] for s in p["scenes"]]
    assert kinds == ["cold_open", "title", "chapter", "end"]
    # scenes are back to back and the total is their sum
    for a, b in zip(p["scenes"], p["scenes"][1:]):
        assert b["from"] == pytest.approx(a["from"] + a["dur"], abs=1e-3)
    assert p["total"] == pytest.approx(p["scenes"][-1]["from"] + p["scenes"][-1]["dur"], abs=1e-3)
    # VO lines never overlap and each sits inside its scene
    vo = sorted(p["vo"], key=lambda c: c["at"])
    for a, b in zip(vo, vo[1:]):
        assert b["at"] >= a["at"] + a["dur"]
    cold = p["scenes"][0]
    assert cold["payoff"]["at"] > cold["beats"][-1]["at"]


def test_cold_open_lines_have_no_subtitle_pill(tmp_path: Path) -> None:
    p = resolve(tmp_path)
    subs = {c["id"]: c["sub"] for c in p["vo"]}
    assert subs["c1"] is False and subs["c3"] is False
    assert subs["t1"] is True and subs["e1"] is True


def test_chapter_label_colours_cycle(tmp_path: Path) -> None:
    def three_chapters(spec: dict) -> None:
        ch = spec["scenes"][2]
        spec["scenes"][3:3] = [copy.deepcopy(ch), copy.deepcopy(ch)]
    p = resolve(tmp_path, three_chapters)
    assert [s["color"] for s in p["scenes"] if s["kind"] == "chapter"] == rv.LABEL_COLORS


@pytest.mark.parametrize("mutate, message", [
    (lambda s: s["scenes"][1].__setitem__("vo", ["nope"]), "unknown vo id"),
    (lambda s: s["scenes"][2]["shots"][0]["camera"].append({"t": 99, "x": 0, "y": 0, "zoom": 1}), "after the shot ends"),
    (lambda s: s["scenes"].pop(1), "title scene is required"),
    (lambda s: s["scenes"].pop(), "last scene must be the end card"),
    (lambda s: s["scenes"][3].__setitem__("subline", "Set up in minutes./p>"), "suspicious text"),
    (lambda s: s["scenes"][1].__setitem__("headline", "Introducing the Attendee App."), "italic"),
    (lambda s: s["scenes"][0]["prop"]["pile"].__setitem__("items", s["scenes"][0]["prop"]["pile"]["items"][:2]), "at least 6 items"),
    (lambda s: s["scenes"][1]["laptop"].__setitem__("src", "../../../secret.png"), "inside the spec folder"),
])
def test_invalid_specs_are_rejected(tmp_path: Path, mutate, message: str) -> None:
    with pytest.raises(rv.SpecError, match=message):
        resolve(tmp_path, mutate)


def test_music_ducks_under_voice() -> None:
    vo = [{"at": 2.0, "dur": 1.0}]
    assert bed.duck(vo, 0.5) == 1.0
    assert bed.duck(vo, 2.5) == pytest.approx(1 - bed.DUCK)
    assert 1 - bed.DUCK < bed.duck(vo, 1.92) < 1.0  # soft edge before the line


def test_frame_centres_region_and_clamps_zoom() -> None:
    # the repro toggle (2127..2202 x 515..555 on a 2304 px wide capture) sits at world (1466, 549)
    key = rv.frame(2304, 2127, 515, 2202, 555)
    assert abs(key["x"] - 1466) <= 2 and abs(key["y"] - 549) <= 2
    assert key["zoom"] == 3.0  # tiny target: clamped
    assert 1.25 < rv.frame(2304, 0, 0, 2304, 1378)["zoom"] < 1.45  # whole page: the screen fills the frame
