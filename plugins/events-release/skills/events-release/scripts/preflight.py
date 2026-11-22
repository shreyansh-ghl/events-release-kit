"""Preflight for an Events release run: every local tool the kit needs, checked before the interview.

    python3 -I preflight.py [--video] [--fix]

--video  also check the video stack (Remotion deps, Voicebox + house voice)
--fix    install what can be installed without the author (Remotion npm deps)

Prints one line per check and exits 1 if anything blocking is missing. Claude-side checks (Chrome extension
connected, ClickUp via ghl-ai, Slack signed in) are done by Claude with its own tools; see SKILL.md step 0.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
VOICEBOX = "http://localhost:17493/health"


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def check_python() -> tuple[bool, str, str]:
    ok = sys.version_info >= (3, 10)
    try:
        import PIL  # noqa: F401
        pil = True
    except ImportError:
        pil = False
    return ok and pil, f"python {sys.version.split()[0]}, Pillow {'ok' if pil else 'missing'}", "python3 -m pip install --user Pillow"


def check_bin(name: str, fix: str, version_arg: str = "--version") -> tuple[bool, str, str]:
    path = shutil.which(name)
    if not path:
        return False, f"{name} not found", fix
    out = run([path, version_arg]).stdout.strip().splitlines()
    return True, f"{name}: {out[0] if out else path}", fix


def check_node() -> tuple[bool, str, str]:
    path = shutil.which("node")
    if not path:
        return False, "node not found", "install Node 20+ (nvm install 20)"
    ver = run([path, "--version"]).stdout.strip()
    major = int(ver.lstrip("v").split(".")[0] or 0)
    return major >= 18, f"node {ver}", "nvm install 20 && nvm use 20"


def check_chrome() -> tuple[bool, str, str]:
    return CHROME.exists(), "Google Chrome app (card renderer)", "install Google Chrome in /Applications"


def check_gh() -> tuple[bool, str, str]:
    if not shutil.which("gh"):
        return False, "gh not found", "brew install gh && gh auth login"
    res = run(["gh", "auth", "status"])
    return res.returncode == 0, "gh signed in" if res.returncode == 0 else "gh not signed in", "gh auth login   (author runs this)"


def check_remotion(fix: bool) -> tuple[bool, str, str]:
    video = KIT / "video"
    present = (video / "node_modules" / "remotion").is_dir()
    if not present and fix:
        res = run(["npm", "ci", "--no-audit", "--no-fund"], cwd=video, timeout=600)
        present = res.returncode == 0 and (video / "node_modules" / "remotion").is_dir()
    return present, "Remotion deps installed" if present else "Remotion deps missing", f"cd {video} && npm ci"


def check_voicebox() -> tuple[bool, str, str]:
    try:
        urllib.request.urlopen(VOICEBOX, timeout=5).read()
    except OSError:
        return False, "Voicebox not running", "open the Voicebox app (it serves localhost:17493), then re-run"
    res = run([sys.executable, "-I", str(KIT / "voice" / "vo.py"), "check"], timeout=120)
    if res.returncode != 0:
        return False, "Voicebox up, house voice check failed", res.stderr.strip()[-200:] or "see voice/vo.py check"
    info = json.loads(res.stdout.strip().splitlines()[-1])
    return True, f"Voicebox up, house voice {info['voice']} seed {info['seed']}", ""


def main(argv: list[str]) -> int:
    video, fix = "--video" in argv, "--fix" in argv
    checks = [
        ("python", check_python()),
        ("node", check_node()),
        ("ffmpeg", check_bin("ffmpeg", "brew install ffmpeg", "-version")),
        ("chrome", check_chrome()),
        ("gh", check_gh()),
        ("swift", check_bin("swift", "xcode-select --install   (author runs this; QA uses macOS Vision OCR)")),
    ]
    if video:
        checks += [("remotion", check_remotion(fix)), ("voicebox", check_voicebox())]
    blocked = False
    for name, (ok, detail, how) in checks:
        print(f"{'ok ' if ok else 'NO '} {name:9} {detail}" + ("" if ok else f"\n      fix: {how}"))
        blocked |= not ok
    print("preflight: " + ("BLOCKED, fix the NO lines first" if blocked else "all clear"))
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
