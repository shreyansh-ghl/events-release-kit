"""Behaviour tests for the one-time setup plan (what gets installed automatically)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import setup  # noqa: E402


def fake_which(present: set[str]):
    return lambda name: f"/opt/homebrew/bin/{name}" if name in present else None


def labels(steps: list[tuple[str, list[str]]]) -> list[str]:
    return [label.split(" ")[0] for label, _ in steps]


def test_fresh_mac_installs_everything_it_can(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(setup.shutil, "which", fake_which({"brew", "npm"}))
    monkeypatch.setattr(setup, "has_pillow", lambda: False)
    monkeypatch.setattr(setup, "KIT", tmp_path)
    assert labels(setup.plan()) == ["Pillow", "ffmpeg", "gh", "video"]


def test_ready_machine_installs_nothing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "video" / "node_modules" / "remotion").mkdir(parents=True)
    monkeypatch.setattr(setup.shutil, "which", fake_which({"brew", "npm", "ffmpeg", "gh"}))
    monkeypatch.setattr(setup, "has_pillow", lambda: True)
    monkeypatch.setattr(setup, "KIT", tmp_path)
    assert setup.plan() == []


def test_without_homebrew_system_tools_are_left_to_the_person(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(setup.shutil, "which", fake_which({"npm"}))
    monkeypatch.setattr(setup, "has_pillow", lambda: True)
    monkeypatch.setattr(setup, "KIT", tmp_path)
    assert labels(setup.plan()) == ["video"]  # preflight then prints the exact fix for ffmpeg and gh


def test_dry_run_changes_nothing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(setup.shutil, "which", fake_which({"brew", "npm"}))
    monkeypatch.setattr(setup, "has_pillow", lambda: False)
    monkeypatch.setattr(setup, "KIT", tmp_path)
    monkeypatch.setattr(setup, "run_step", lambda *a: pytest.fail("dry run must not install"))
    assert setup.main(["setup.py", "--dry-run"]) == 0
    assert "would install Pillow" in capsys.readouterr().out
