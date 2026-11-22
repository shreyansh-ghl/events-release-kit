---
name: events-release
description: Make the release pack for something the HighLevel Events team shipped (narrated house-style video, release note, screenshot cards) and post it for review in #events-core-internal. Reads the ClickUp task and PRs first, interviews the author only for gaps, captures real screens from the Northstar staging sub-account in Chrome, and stops at two checkpoints. Use when an Events teammate says "release note", "release video", "we shipped X", or runs /events-release.
---

# Events release kit

One run = one shipped thing = one pack: up to **9 images + 1 video** (< 100 MB) and a release note in the team format.
Every pack looks and sounds the same whoever runs it: house look (`tokens.json`), house voice (`voice/`), shared
fictional world (`northstar/world.json`), real product UI.

`KIT` = this skill's folder. `RUN` = the run folder `run.py new` prints (`~/events-release-runs/<date>-<slug>/`).

## Non-negotiables (read `reference/guardrails.md` once per run)

- **Real UI only, fictional data only.** Capture the Northstar staging sub-account; never invent UI, never show real people, brands or staging junk.
- **Read-only outside Northstar.** In Northstar, write only what the feature needs, and only after the author says yes.
- **The author types every password and code.** Never read or print credential files.
- **Claude never decides on the video**: the author does (default yes). **Claude never opens or submits the Release Update Form.**
- **Post only after the author says "post it"**, from the author's own Slack in Chrome, never as a bot.
- **Two checkpoints, no more:** A after capture, B on the final pack.

## Progress

Every stage starts with `python3 -I KIT/scripts/run.py stage RUN <stage> doing` and ends with `... done`
(or `blocked --note "why"`). When waiting on the author: `run.py ask RUN "what they must do"`; clear it with `run.py ask RUN ""`.
The build sessions and the plugin's progress band read `RUN/status.json`; keep it true. The band (installed with this
plugin) shows above the prompt: phase bar, both sessions, and the author's ask in amber; `/release-progress` re-shows it.

## 0 · Preflight (fail fast, before any question)

1. Ask for the ClickUp link(s) and PR link(s) in one short chat line if the author hasn't given them, and a short slug.
2. `python3 -I KIT/scripts/run.py new <slug> --title "<working title>" --author "<name>"` → `RUN`. Re-running resumes.
3. `python3 -I KIT/scripts/preflight.py --video --fix`. Fix what you can; give the author exact commands for the rest.
4. Claude-side checks, all before the interview:
   - **Chrome:** load the Claude-in-Chrome tools in one ToolSearch; `list_connected_browsers` must show one. If none, stop and tell the author to open Chrome with the extension signed in, then retry.
   - **Slack:** a Chrome tab on `app.slack.com` signed in to the HighLevel workspace (look, don't post).
   - **ClickUp:** `mcp__ghl-ai__mcp_execute_tool` → `clickup_get-task` on the given task must return it.
   - **GitHub:** `gh pr view <url> --json title` works.
   Only check Voicebox again later if the author turns the video off.

## 1 · Read (facts before questions)

- ClickUp: `clickup_get-task` (+ `clickup_get-task-comments` when the description is thin). Results are large and get
  saved to a file: condense with `python3 -I KIT/scripts/facts.py clickup <saved file>`.
- PRs: `python3 -I KIT/scripts/facts.py pr <url> ...` (title, body, reviewers without bots, changed areas).
- Append both outputs to `RUN/brief.md` → "Facts"; never paste raw dumps into the chat.
- Derive: what changed for users, which surfaces (see `reference/interview.md` § surfaces), who reviewed (thanks list), flags, plans.
- Play back **5 lines**: what shipped, for whom, where it lives, surfaces, availability.

## 2 · Interview (only the gaps)

Follow `reference/interview.md`: two `AskUserQuestion` rounds max, defaults pre-selected from the facts, free text only where
needed. Record answers in `brief.md` → "Interview"; `run.py set RUN video=yes|no`.

## 3 · Northstar check

Follow `reference/northstar.md`: the event exists, is published, dates are upcoming, key data is present, and anything
this feature needs is seeded (author approves each create; add new fictional records to `northstar/world.json`).

## 4 · Capture + cards

Follow `reference/capture.md`:
1. Write the **shot plan** (`RUN/shots/plan.json`): ≤ 9 cards (hero first) + the video's screens. `run.py set RUN shots=<n>`.
2. Web shots in Chrome (Builder, public page, Client Portal): zoom tiles → `KIT/scripts/tiles.py stitch`. Read-only; Cancel dialogs.
3. Mobile: write `RUN/shots/phone-shotlist.md`, show it, `run.py ask` the author for phone screenshots in `RUN/shots/raw/phone/`.
4. Write a card spec per card (`RUN/shots/specs/NN-<id>.json`) and render with `KIT/cards/render_card.py` → `RUN/shots/final/`.
5. Write the **story paragraph** (problem → what's new → payoff, 4–6 sentences) and the headline into `brief.md` → "Story".

## ── Checkpoint A ──

Show: contact sheet (`tiles.py sheet RUN/qa/checkpoint-a.png RUN/shots/final/*.png`), the story paragraph, headline,
release type + label, and (if video) the 1-line arc per chapter. Ask with `AskUserQuestion`: Approve · Change shots ·
Change story. Loop on changes until approved. Record "Checkpoint A approved <time>" in `brief.md`.

## 5 · Build (two sessions in parallel)

Start both workers in **one message** with the `Agent` tool (`subagent_type: general-purpose`, names `video` and
`note`); each prompt is just: "Read `KIT/workers/<video|note>-session.md` and follow it. KIT=<abs path>. RUN=<abs path>."
Skip `video` when the author said no. While they run, the main session stays with the author (it is the only one that
drives Chrome or asks questions) and watches `run.py show RUN`. Each worker reports back when done; relay the
essentials, never fabricate a result that hasn't arrived.

## 6 · QA

`python3 -I KIT/scripts/qa.py RUN` checks limits (≤ 9 cards at 3200×2000, video < 100 MB, 30–120 s), OCRs every card
and a frame every 2 s of the video (staging junk, real-world names, non-fictional emails, stray HTML like `./p>`), and
lints the note (team format, no `**`/`#`, no placeholders). ERRORs block; WARNs are shown to the author. Route each
error to its owner (card → fix here; video → `SendMessage` to `video`; copy → `SendMessage` to `note`) and re-run until
it passes. Author-approved exceptions go in `RUN/qa/allow.txt`.

## ── Checkpoint B ──

Show the final pack: `RUN/video/video.mp4`, `RUN/note/review-post.md`, a contact sheet of `RUN/shots/final/`, and the
QA warnings. Route change requests with `SendMessage` to the owning worker (note text → `note`; video → `video`;
image → re-render the card here), then re-run QA. Approved = the author says "post it".

## 7 · Post (only after "post it")

Follow `reference/post.md`: Chrome → Slack `#events-core-internal` as the author, text + video + images, @mentions picked
from Slack's own dropdown. Report the message link; `run.py set RUN post_url=<link>`.

## 8 · Handoff

Give the author `RUN/note/form-handoff.md` (every Release Update Form field, copy-ready, plus the upload list). They file
the form themselves after the teams approve. Mark `handoff done`.
