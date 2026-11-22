"""Condense ClickUp tasks and GitHub PRs into the "Facts" section of brief.md (markdown on stdout).

    python3 -I facts.py clickup <saved_result.txt|.json> ...   # file(s) the ghl-ai clickup_get-task result was saved to
    python3 -I facts.py pr <pr_url> ...                        # runs gh pr view for each PR

ClickUp results are large (dozens of custom fields); only what a release note needs is kept.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

MAX_TEXT = 2500
BOTS = re.compile(r"\[bot\]$|[-_.]bot$|^(sentry|codecov|github-actions|dependabot|copilot|orca|sonar|snyk|coderabbit|renovate)", re.I)


def load_task(path: Path) -> dict:
    raw = path.read_text()
    start = raw.find("{")
    if start < 0:
        raise ValueError(f"{path}: no JSON found")
    data = json.loads(raw[start:])
    return data.get("result", data) if isinstance(data, dict) else data


def clickup_md(task: dict) -> str:
    text = (task.get("text_content") or task.get("description") or "").strip()
    if len(text) > MAX_TEXT:
        text = text[:MAX_TEXT] + " …(trimmed)"
    people = ", ".join(a.get("username") or a.get("email", "?").split("@")[0] for a in task.get("assignees") or [])
    lines = [
        f"### ClickUp: {task.get('name', '?')}",
        f"- Link: {task.get('url', '?')}",
        f"- Status: {(task.get('status') or {}).get('status', '?')} · List: {(task.get('list') or {}).get('name', '?')}",
        f"- Assignees: {people or '—'}",
    ]
    tags = [t.get("name") for t in task.get("tags") or [] if t.get("name")]
    if tags:
        lines.append(f"- Tags: {', '.join(tags)}")
    for cl in task.get("checklists") or []:
        items = [i.get("name", "") for i in cl.get("items") or []]
        if items:
            lines.append(f"- Checklist {cl.get('name', '')}: " + "; ".join(items))
    lines += ["", "Description:", "", text or "(empty)", ""]
    return "\n".join(lines)


def pr_md(url: str) -> str:
    fields = "title,body,author,reviews,mergedAt,state,url,files,headRepository"
    res = subprocess.run(["gh", "pr", "view", url, "--json", fields], capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        raise RuntimeError(f"gh pr view {url}: {res.stderr.strip()}")
    pr = json.loads(res.stdout)
    reviewers = sorted({r["author"]["login"] for r in pr.get("reviews") or [] if r.get("author") and not BOTS.search(r["author"]["login"])})
    files = [f["path"] for f in pr.get("files") or []]
    body = re.sub(r"<!--.*?-->", "", pr.get("body") or "", flags=re.S).strip()
    if len(body) > MAX_TEXT:
        body = body[:MAX_TEXT] + " …(trimmed)"
    top_dirs = sorted({"/".join(p.split("/")[:3]) for p in files})[:25]
    return "\n".join([
        f"### PR: {pr['title']}",
        f"- Link: {pr['url']} · {pr['state']}" + (f" · merged {pr['mergedAt'][:10]}" if pr.get("mergedAt") else ""),
        f"- Repo: {(pr.get('headRepository') or {}).get('name', '?')} · Author: {pr['author']['login']}",
        f"- Reviewers (thanks list): {', '.join(reviewers) or '—'}",
        f"- Changed areas ({len(files)} files): {', '.join(top_dirs)}",
        "", "Description:", "", body or "(empty)", "",
    ])


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] not in ("clickup", "pr"):
        print(__doc__)
        return 2
    try:
        for arg in argv[2:]:
            print(clickup_md(load_task(Path(arg))) if argv[1] == "clickup" else pr_md(arg))
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as err:
        print(f"facts.py: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
