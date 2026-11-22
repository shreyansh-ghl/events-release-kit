"""Behaviour tests for the run folder + status.json helper."""
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run  # noqa: E402


@pytest.fixture()
def run_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("EVENTS_RELEASE_RUNS", str(tmp_path))
    return run.new("coupon-codes", "Coupon codes", "Jordan")


def status(d: Path) -> dict:
    return json.loads((d / "status.json").read_text())


def test_new_creates_folders_and_resumes(run_dir: Path) -> None:
    for f in run.FOLDERS:
        assert (run_dir / f).is_dir()
    assert status(run_dir)["stage"] == "preflight"
    run.set_stage(run_dir, "preflight", "done")
    assert run.new("coupon-codes", "Other title", "X") == run_dir  # same day + slug resumes, keeps state
    assert status(run_dir)["stages"]["preflight"]["state"] == "done"


def test_bad_slug_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVENTS_RELEASE_RUNS", str(tmp_path))
    with pytest.raises(ValueError):
        run.new("Coupon Codes!", "x", "y")


def test_stage_flow_moves_current_stage(run_dir: Path) -> None:
    run.set_stage(run_dir, "preflight", "doing")
    assert status(run_dir)["stage"] == "preflight"
    run.set_stage(run_dir, "preflight", "done")
    assert status(run_dir)["stage"] == "read"
    run.set_stage(run_dir, "capture", "blocked", "waiting for phone shots")
    s = status(run_dir)
    assert s["stage"] == "capture" and s["stages"]["capture"]["note"] == "waiting for phone shots"


def test_shot_limit_enforced(run_dir: Path) -> None:
    run.set_fields(run_dir, ["shots=9", "video=no"])
    assert status(run_dir)["shots"] == 9 and status(run_dir)["video"] == "no"
    with pytest.raises(ValueError, match="at most 9"):
        run.set_fields(run_dir, ["shots=10"])


def test_unknown_field_and_state_rejected(run_dir: Path) -> None:
    with pytest.raises(ValueError):
        run.set_fields(run_dir, ["stage=done"])
    with pytest.raises(ValueError):
        run.set_stage(run_dir, "capture", "finished")


def test_parallel_session_updates_do_not_lose_writes(run_dir: Path) -> None:
    def worker(name: str) -> None:
        for i in range(25):
            run.set_session(run_dir, name, "doing", step=f"{i}")
    threads = [threading.Thread(target=worker, args=(n,)) for n in run.SESSIONS]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    s = status(run_dir)
    assert all(s["sessions"][n]["step"] == "24" for n in run.SESSIONS)


def test_ask_shows_in_summary(run_dir: Path) -> None:
    run.set_ask(run_dir, "Send phone shots p1-p3")
    assert "WAITING ON AUTHOR: Send phone shots p1-p3" in run.show(run_dir)
    run.set_ask(run_dir, "")
    assert "WAITING" not in run.show(run_dir)
