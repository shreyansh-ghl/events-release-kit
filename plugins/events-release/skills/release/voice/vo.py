"""Generate house-voice VO lines with Voicebox.

Usage:
    python3 vo.py check
    python3 vo.py line "Text to say." "Direction for this line." out.wav
    python3 vo.py script script.json out_dir/ [--only s2,s5]

--only regenerates just those ids and merges them into the existing vo-manifest.json.
Every line is pace-checked: outside 1.8-4.2 words/s it is flagged PACE (change the direction or text, then --only it).

script.json: [{"id": "s01", "text": "...", "direction": "..."}, ...]
Writes out_dir/<id>.wav and out_dir/vo-manifest.json (id, text, duration seconds).
Needs the Voicebox app running (server on localhost:17493).
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "voice.json").read_text())
BASE = "http://localhost:17493"


def call(method: str, path: str, body: dict | None = None, raw: bool = False) -> object:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        payload = resp.read()
    return payload if raw else json.loads(payload or b"null")


def server_up() -> bool:
    try:
        call("GET", "/health")
        return True
    except (urllib.error.URLError, ConnectionError, TimeoutError):
        return False


def profile_id() -> str:
    """Find the house profile, creating it from voice.json if this machine lacks it."""
    want = CFG["profile"]
    for p in call("GET", "/profiles"):
        if p.get("preset_voice_id") == want["preset_voice_id"] and p.get("preset_engine") == want["preset_engine"]:
            return p["id"]
    return call("POST", "/profiles", want)["id"]


def instruct(direction: str) -> str:
    text = (CFG["base_instruct"] + " " + (direction or "").strip()).strip()
    if len(text) > 500:
        raise ValueError(f"instruct is {len(text)} chars; shorten the direction (max 500 total)")
    return text


def generate(text: str, direction: str, out_path: str | Path) -> dict:
    body = dict(CFG["generate"], profile_id=profile_id(), text=text, instruct=instruct(direction))
    gen = call("POST", "/generate", body)
    gid = gen["id"]
    # /generate/{id}/status is a server-sent event stream; poll the JSON history record instead.
    for _ in range(600):
        info = call("GET", f"/history/{gid}")
        state = info.get("status")
        if state == "completed":
            break
        if state in ("failed", "cancelled"):
            raise RuntimeError(f"generation {gid} {state}: {info.get('error')}")
        time.sleep(1)
    else:
        raise TimeoutError(f"generation {gid} did not finish in 10 minutes")
    audio = call("GET", f"/history/{gid}/export-audio", raw=True)
    Path(out_path).write_bytes(audio)
    return {"generation_id": gid, "duration": info.get("duration")}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in ("check", "line", "script"):
        print(__doc__)
        return 2
    if not server_up():
        print("Voicebox server not reachable on localhost:17493. Open the Voicebox app and retry.", file=sys.stderr)
        return 1
    if argv[1] == "check":
        print(json.dumps({"server": "up", "profile_id": profile_id(), "voice": CFG["profile"]["preset_voice_id"],
                          "seed": CFG["generate"]["seed"]}))
        return 0
    if argv[1] == "line":
        text, direction, out = argv[2], argv[3], argv[4]
        print(json.dumps(generate(text, direction, out)))
        return 0
    script, out_dir = json.loads(Path(argv[2]).read_text()), Path(argv[3])
    only = set(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
    out_dir.mkdir(parents=True, exist_ok=True)
    mpath = out_dir / "vo-manifest.json"
    old = {m["id"]: m for m in json.loads(mpath.read_text())} if only and mpath.is_file() else {}
    manifest, slow = [], []
    for line in script:
        if only is not None and line["id"] not in only and line["id"] in old:
            entry = old[line["id"]]
        else:
            res = generate(line["text"], line.get("direction", ""), out_dir / f"{line['id']}.wav")
            entry = {"id": line["id"], "text": line["text"], **res}
        manifest.append(entry)
        wps = pace(entry["text"], entry.get("duration") or 0)
        flag = "" if 1.8 <= wps <= 4.2 else "  PACE"
        if flag:
            slow.append(entry["id"])
        print(f"{entry['id']}: {entry.get('duration')}s, {wps:.1f} words/s{flag}", flush=True)
    mpath.write_text(json.dumps(manifest, indent=2))
    if slow:
        print(f"pace outside 1.8-4.2 words/s: {', '.join(slow)}", file=sys.stderr)
    return 0


def pace(text: str, duration: float) -> float:
    """Spoken words per second (one-word lines are allowed to be slow)."""
    words = len(text.split())
    if words <= 2:
        return 2.5
    return words / duration if duration else 0.0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
