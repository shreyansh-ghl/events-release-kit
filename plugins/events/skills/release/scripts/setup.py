"""One-time setup after installing the plugin: install what can be installed, then list what the person must do.

    python3 -I setup.py            # install missing pieces, then run the full preflight
    python3 -I setup.py --dry-run  # only say what it would install

Installs without asking (all local, reversible): Pillow for this Python, ffmpeg and gh via Homebrew, the video
template's npm packages. Never signs in to anything and never touches credentials: sign-ins, app installs (Voicebox,
Chrome extension) and Northstar access are printed as steps for the person.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
PERSON_STEPS = [
    "Install the Claude in Chrome extension in Google Chrome and sign it in (it must show as connected).",
    "In that Chrome, sign in to staging (staging.gohighlevel.com) and to Slack (app.slack.com).",
    "Install and open the Voicebox app (local text-to-speech on localhost:17493); the kit creates the narrator itself.",
    "Ask the kit owner for a user on the Northstar Collective staging sub-account.",
    "Make sure the ghl-ai MCP is connected in Claude Code (it reads ClickUp).",
]


def has_pillow() -> bool:
    res = subprocess.run([sys.executable, "-c", "import PIL"], capture_output=True)
    return res.returncode == 0


def plan() -> list[tuple[str, list[str]]]:
    """What to install on this machine: (label, command) pairs, in order."""
    steps: list[tuple[str, list[str]]] = []
    brew = shutil.which("brew")
    if not has_pillow():
        steps.append(("Pillow (pip, user install)", [sys.executable, "-m", "pip", "install", "--user", "--quiet", "Pillow"]))
    for tool, formula in (("ffmpeg", "ffmpeg"), ("gh", "gh")):
        if not shutil.which(tool) and brew:
            steps.append((f"{tool} (Homebrew)", [brew, "install", formula]))
    if shutil.which("npm") and not (KIT / "video" / "node_modules" / "remotion").is_dir():
        steps.append(("video template packages (npm ci)", ["npm", "ci", "--no-audit", "--no-fund", "--prefix", str(KIT / "video")]))
    return steps


def run_step(label: str, cmd: list[str]) -> bool:
    print(f"installing {label} ...", flush=True)
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if res.returncode == 0:
        return True
    if "Pillow" in label and "externally-managed" in (res.stderr + res.stdout) and shutil.which("brew"):
        # Homebrew's Python refuses pip installs; Homebrew ships Pillow as a formula instead
        res = subprocess.run([shutil.which("brew") or "brew", "install", "pillow"], capture_output=True, text=True, timeout=900)
        if res.returncode == 0:
            return True
    print(f"  could not install {label}: {(res.stderr or res.stdout).strip()[-300:]}", file=sys.stderr)
    return False


def main(argv: list[str]) -> int:
    steps = plan()
    if "--dry-run" in argv:
        for label, cmd in steps:
            print(f"would install {label}: {' '.join(cmd)}")
        if not steps:
            print("nothing to install")
        return 0
    failed = [label for label, cmd in steps if not run_step(label, cmd)]
    print("\nchecking everything ...", flush=True)
    pre = subprocess.run([sys.executable, "-I", str(KIT / "scripts" / "preflight.py"), "--video", "--fix"])
    print("\nThings only you can do (once):")
    for i, step in enumerate(PERSON_STEPS, 1):
        print(f"  {i}. {step}")
    if failed:
        print(f"\nCould not install automatically: {', '.join(failed)} (see the messages above).")
    print("\nThen restart Claude Code and run /events:release, or say: make the release pack for <ClickUp link> <PR link>.")
    return 1 if failed or pre.returncode else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
