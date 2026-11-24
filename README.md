# Events release kit

A Claude Code plugin for the HighLevel Events team. Tell Claude what you shipped and it makes the whole release pack:
a narrated house-style video, up to 9 screenshot cards, the release note in the team format, and the Release Update
Form handoff. Same theme, same voice and the same fictional Northstar world whoever makes it; real product UI only.

## Install

Say this to Claude Code:

> install https://github.com/shreyansh-ghl/events-release-kit

That's it. When it's done, restart Claude Code and run **`/events:release`**.

---

### Installing with Claude (instructions for Claude)

When someone asks you to install this repository, do exactly this, in order, and tell them briefly what you did.

1. Install the plugin with the `claude` CLI:

   ```bash
   claude plugin marketplace add shreyansh-ghl/events-release-kit 2>/dev/null || claude plugin marketplace update events-release-kit
   claude plugin install events@events-release-kit
   ```

   If `claude plugin` is not available (no `claude` on PATH, or it errors), ask the person to type these two lines in
   the Claude Code prompt themselves, one at a time, then continue with step 2:
   `/plugin marketplace add shreyansh-ghl/events-release-kit` and `/plugin install events@events-release-kit`.

2. Run the one-time setup (it installs Pillow, ffmpeg, gh and the video packages itself, then checks everything):

   ```bash
   python3 -I "$(ls -d ~/.claude/plugins/cache/events-release-kit/events/*/ | sort -V | tail -1)skills/release/scripts/setup.py"
   ```

   (If `CLAUDE_CONFIG_DIR` is set, use it instead of `~/.claude`.)

3. Show the person the "Things only you can do" list the setup prints (Chrome extension, staging + Slack sign-in,
   Voicebox, Northstar access, ghl-ai MCP). Do not do those for them: they involve their accounts and apps.

4. Tell them to restart Claude Code, then run `/events:release` (or say "make the release pack for
   <ClickUp link> <PR link>").

---

## Use

Run `/events:release`, or just say what you shipped:

> Make the release pack for coupon codes: https://app.clickup.com/t/… https://github.com/GoHighLevel/…/pull/…

The kit then:

1. **Preflight**: checks tools, Chrome, Slack, ClickUp and GitHub before asking you anything.
2. **Reads** the ClickUp task and PRs, and plays back what it understood in 5 lines.
3. **Interviews** you only for the gaps (release type, label, surfaces, video yes/no, availability…).
4. **Checks Northstar**: the demo event is there and its dates are still upcoming.
5. **Captures** real screens in your Chrome (read-only outside Northstar) and asks for phone screenshots if the mobile
   app is involved; renders the cards. For the video it plans one journey through the feature and captures every
   click as a real before/after frame, so the video shows the product doing the work, not a tour of settings.
6. **Checkpoint A**: you approve the shots, the one-paragraph story and the video storyboard.
7. **Builds** the video and the note in two parallel sessions. You approve the voice-over script before any voice is made.
8. **QA**: OCR on every image and video frame (no real names, no staging junk, no stray HTML), note format lint, size limits.
9. **Checkpoint B**: you review the pack; changes go back to the right session.
10. **Posts** to `#events-core-internal` from your own Slack, only after you say "post it".
11. **Hands off** the Release Update Form fields. You file the form yourself.

A band above the prompt follows the run: a phase bar (Prepare › Capture › Build › Review › Ship), the video and note
sessions live (running time, how full their context is, done or stopped), and an amber "Your turn" when it needs you.
`/release-progress` brings it back if you hide it. Runs live in `~/events-release-runs/<date>-<slug>/`.

Update to the latest version: `claude plugin marketplace update events-release-kit`, then restart Claude Code.

## Rules the kit enforces

- Real UI only, fictional data only (the Northstar world), read-only outside the Northstar sub-account.
- You type every password and code; nothing is posted until you say "post it"; the Release Update Form is yours.
- One release note per thing shipped; a post holds at most 9 images + 1 video (< 100 MB).

## What's inside

```
plugins/events/
  skills/release/      the skill: SKILL.md, reference/ (guardrails, interview, capture, note format…),
                       workers/ (video + note session prompts), scripts/ (setup, run state, preflight, capture, QA),
                       cards/ (card renderer), video/ (Remotion template + music bed), voice/ (house voice),
                       northstar/ (the shared fictional world + brand art), fonts/, tokens.json (house look)
  hooks/register.tsx   the progress band above the prompt
```

Tests: `uvx --with pillow pytest tests -q` in `skills/release/` and in `skills/release/video/`;
`claude plugin test plugins/events` for the band. Fonts are under the SIL Open Font License. The band's live
worker tracking follows the approach of [savvy-progress](https://github.com/johnnyvizz/claude-kit/tree/main/plugins/savvy-progress) (MIT).
