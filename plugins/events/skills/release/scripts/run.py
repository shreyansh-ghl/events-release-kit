"""Run folder + status.json for one Events release (the progress mod and every session read this file).

    python3 -I run.py new <slug> --title "Coupon codes" --author "Jordan"   # prints the run dir
    python3 -I run.py stage   <run_dir> <stage> <todo|doing|done|blocked|skipped> [--note "..."]
    python3 -I run.py session <run_dir> <video|note> <todo|doing|done|blocked|skipped> [--step "VO 4/9"] [--note "..."]
    python3 -I run.py ask     <run_dir> "What the author must do now"       # shows in the mod; "" clears it
    python3 -I run.py set     <run_dir> key=value ...                       # top-level fields, e.g. video=no shots=7
    python3 -I run.py show    <run_dir>

Runs live in ~/events-release-runs/<yyyy-mm-dd>-<slug>/ (override with EVENTS_RELEASE_RUNS).
Writes are locked and atomic, so parallel sessions can update their own parts safely.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

STAGES = ["preflight", "read", "interview", "northstar", "capture", "checkpoint_a", "build", "qa", "checkpoint_b", "post", "handoff"]
SESSIONS = ["video", "note"]
STATES = {"todo", "doing", "done", "blocked", "skipped"}
FOLDERS = ["shots/raw/web", "shots/raw/phone", "shots/final", "shots/specs", "video", "note", "qa"]
MAX_SHOTS = 9


def runs_root() -> Path:
    return Path(os.environ.get("EVENTS_RELEASE_RUNS", Path.home() / "events-release-runs"))


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fresh_status(slug: str, title: str, author: str) -> dict:
    return {
        "slug": slug,
        "title": title,
        "author": author,
        "created": now(),
        "updated": now(),
        "stage": "preflight",
        "ask": "",
        "video": "yes",
        "shots": 0,
        "max_shots": MAX_SHOTS,
        "video_mb": None,
        "post_url": None,
        "stages": {s: {"state": "todo", "note": "", "at": None} for s in STAGES},
        "sessions": {s: {"state": "todo", "step": "", "note": "", "at": None} for s in SESSIONS},
    }


@contextmanager
def locked(run_dir: Path) -> Iterator[dict]:
    """Read-modify-write status.json under an exclusive lock; written atomically on exit."""
    path = run_dir / "status.json"
    if not path.is_file():
        raise FileNotFoundError(f"no status.json in {run_dir} (create the run with: run.py new <slug>)")
    with open(run_dir / ".status.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = json.loads(path.read_text())
        yield data
        data["updated"] = now()
        fd, tmp = tempfile.mkstemp(dir=run_dir, prefix=".status.", suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)


def new(slug: str, title: str, author: str) -> Path:
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        raise ValueError("slug must be lowercase words joined by '-', e.g. coupon-codes")
    run_dir = runs_root() / f"{datetime.now().strftime('%Y-%m-%d')}-{slug}"
    if (run_dir / "status.json").exists():
        return run_dir  # resume
    for f in FOLDERS:
        (run_dir / f).mkdir(parents=True, exist_ok=True)
    (run_dir / "status.json").write_text(json.dumps(fresh_status(slug, title, author), indent=2))
    (run_dir / "brief.md").write_text(f"# {title}\n\n## Facts (ClickUp + PRs)\n\n## Interview\n\n## Story\n\n## Shot plan\n")
    return run_dir


def set_stage(run_dir: Path, stage: str, state: str, note: str = "") -> None:
    if stage not in STAGES or state not in STATES:
        raise ValueError(f"stage must be one of {STAGES}; state one of {sorted(STATES)}")
    with locked(run_dir) as s:
        s["stages"][stage] = {"state": state, "note": note, "at": now()}
        if state in ("doing", "blocked"):
            s["stage"] = stage
        elif state in ("done", "skipped") and s["stage"] == stage:
            nxt = STAGES.index(stage) + 1
            s["stage"] = STAGES[nxt] if nxt < len(STAGES) else "done"


def set_session(run_dir: Path, name: str, state: str, step: str = "", note: str = "") -> None:
    if name not in SESSIONS or state not in STATES:
        raise ValueError(f"session must be one of {SESSIONS}; state one of {sorted(STATES)}")
    with locked(run_dir) as s:
        s["sessions"][name] = {"state": state, "step": step, "note": note, "at": now()}


def set_fields(run_dir: Path, pairs: list[str]) -> None:
    allowed = {"title", "author", "video", "shots", "video_mb", "post_url"}
    with locked(run_dir) as s:
        for pair in pairs:
            key, _, val = pair.partition("=")
            if key not in allowed:
                raise ValueError(f"cannot set {key!r}; allowed: {sorted(allowed)}")
            s[key] = int(val) if key == "shots" else float(val) if key == "video_mb" else val
        if s["shots"] > MAX_SHOTS:
            raise ValueError(f"{s['shots']} shots planned; a release post holds at most {MAX_SHOTS} images + 1 video")


def set_ask(run_dir: Path, text: str) -> None:
    with locked(run_dir) as s:
        s["ask"] = text


def show(run_dir: Path) -> str:
    s = json.loads((run_dir / "status.json").read_text())
    marks = {"todo": " ", "doing": ">", "done": "x", "blocked": "!", "skipped": "-"}
    lines = [f"{s['title']}  ({s['slug']}, video={s['video']}, shots={s['shots']}/{s['max_shots']})"]
    lines += [f"  [{marks[v['state']]}] {k}{'  - ' + v['note'] if v['note'] else ''}" for k, v in s["stages"].items()]
    lines += [f"  session {k}: {v['state']} {v['step']}".rstrip() for k, v in s["sessions"].items()]
    if s["ask"]:
        lines.append(f"  WAITING ON AUTHOR: {s['ask']}")
    return "\n".join(lines)


def _opt(args: list[str], name: str) -> str:
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else ""


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, args = argv[1], argv[2:]
    try:
        if cmd == "new":
            print(new(args[0], _opt(args, "--title") or args[0], _opt(args, "--author")))
        elif cmd == "stage":
            set_stage(Path(args[0]), args[1], args[2], _opt(args, "--note"))
        elif cmd == "session":
            set_session(Path(args[0]), args[1], args[2], _opt(args, "--step"), _opt(args, "--note"))
        elif cmd == "ask":
            set_ask(Path(args[0]), args[1] if len(args) > 1 else "")
        elif cmd == "set":
            set_fields(Path(args[0]), args[1:])
        elif cmd == "show":
            print(show(Path(args[0])))
        else:
            print(__doc__)
            return 2
    except (ValueError, FileNotFoundError, IndexError) as err:
        print(f"run.py {cmd}: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
