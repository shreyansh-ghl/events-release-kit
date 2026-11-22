# Events release kit

A Claude Code plugin for the HighLevel Events team. Tell Claude what you shipped and it makes the whole release pack:

- a **narrated release video** (30–120 s) in the house style, with the house AI voice,
- up to **9 screenshot cards** (3200×2000) in the house look,
- the **release note** in the team format, ready for `#events-core-internal`,
- a **form handoff** file for the Release Update Form.

Every pack looks and sounds the same whoever makes it: one theme, one voice, one fictional world (the Northstar staging
sub-account), real product UI only. A band above the Claude Code prompt shows progress while it runs.

## Install (one line)

```bash
claude plugin marketplace add shreyansh-ghl/events-release-kit && claude plugin install events-release@events-release-kit
```

Or inside Claude Code: `/plugin marketplace add shreyansh-ghl/events-release-kit`, then
`/plugin install events-release@events-release-kit`. Restart Claude Code (or start a new session) afterwards.

Update later with `claude plugin marketplace update events-release-kit`.

## First-time setup

The kit checks all of this itself at the start of every run (preflight) and tells you the exact fix for anything missing.

| Needed for | What |
|---|---|
| Everything | macOS, Python 3.10+ with Pillow (`python3 -m pip install --user Pillow`), Node 20+, `ffmpeg`, Google Chrome, `gh` signed in (`gh auth login`), Xcode command line tools (`xcode-select --install`) |
| Screens + posting | The **Claude in Chrome** extension, connected, in a Chrome where you are signed in to staging and Slack |
| ClickUp | The `ghl-ai` MCP connected in Claude Code |
| Video | The **Voicebox** app running (local text-to-speech on `localhost:17493`); the kit creates the house narrator profile on first run. Remotion's npm packages install themselves on the first run |
| Northstar | A user on the Northstar Collective staging sub-account (ask the kit owner) |

## Use

In Claude Code, say what you shipped:

> Make the release pack for coupon codes: https://app.clickup.com/t/… and https://github.com/GoHighLevel/…/pull/…

or run `/events-release:events-release`. The kit then:

1. **Preflight**: checks tools, Chrome, Slack, ClickUp and GitHub before asking you anything.
2. **Reads** the ClickUp task and PRs, and plays back what it understood in 5 lines.
3. **Interviews** you only for the gaps (release type, label, surfaces, video yes/no, availability…).
4. **Checks Northstar**: the demo event is there and its dates are still upcoming.
5. **Captures** real screens in your Chrome (read-only outside Northstar) and asks you for phone screenshots if the
   mobile app is involved; renders the cards.
6. **Checkpoint A**: you approve the shots and the one-paragraph story.
7. **Builds** the video and the note in two parallel sessions.
8. **QA**: OCR on every image and video frame (no real names, no staging junk, no stray HTML), note format lint, size limits.
9. **Checkpoint B**: you review the pack; changes go back to the right session.
10. **Posts** to `#events-core-internal` from your own Slack, only after you say "post it".
11. **Hands off** the Release Update Form fields. You file the form yourself.

Runs live in `~/events-release-runs/<date>-<slug>/`. The progress band follows them; `/release-progress` brings it back
if you hide it.

## Rules the kit enforces

- Real UI only, fictional data only (the Northstar world), read-only outside the Northstar sub-account.
- You type every password and code; nothing is posted until you say "post it"; the Release Update Form is yours.
- One release note per thing shipped; a post holds at most 9 images + 1 video (< 100 MB).

## What's inside

```
plugins/events-release/
  skills/events-release/   the skill: SKILL.md, reference/ (guardrails, interview, capture, note format…),
                           workers/ (video + note session prompts), scripts/ (run state, preflight, capture, QA),
                           cards/ (card renderer), video/ (Remotion template + music bed), voice/ (house voice),
                           northstar/ (the shared fictional world + brand art), fonts/, tokens.json (house look)
  hooks/register.tsx       the progress band above the prompt
```

Tests: `uvx --with pillow pytest tests -q` in `skills/events-release/` and in `skills/events-release/video/`;
`claude plugin test plugins/events-release` for the band. Fonts are under the SIL Open Font License.
