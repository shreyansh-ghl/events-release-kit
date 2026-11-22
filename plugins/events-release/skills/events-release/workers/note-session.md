# Note session (runs in parallel with the video session)

You write the release note, the Slack review post and the Release Update Form handoff for one Events release.
You are given `KIT` (the events-release skill folder) and `RUN` (the run folder). Checkpoint A is approved.

## Rules
- Work only inside `RUN/note/`. Never edit `KIT`. Never use a browser, never post, never message anyone.
- Every claim comes from `RUN/brief.md` (ClickUp, PRs, interview, approved story). Nothing the product doesn't do.
- "Northstar" is screenshot data only: it never appears in the note.
- Read `KIT/reference/guardrails.md`, `KIT/reference/note-template.md` and `KIT/reference/note-examples.md` first.
- Progress: `python3 -I KIT/scripts/run.py session RUN note doing --step "<step>"`; `done` at the end.

## 1. Release note (step "note") → `RUN/note/release-note.md`
Fill the team format exactly (dashes, `:gohighlevel:` headline line, field order, blank lines). Headline = the approved
headline from the brief. Overview = the approved story paragraph, tightened into 2–4 short paragraphs. 2–8 "What's New"
sub-features, each with its own emoji. Roles in "Why This Matters" only where they apply. "How to Get Started" uses the
real UI path exactly as the captured screens show it (not the brief's wording). Special thanks from the brief's thanks list (people only, no bots), one line per role saying what they did. CC = default + extra teams from the interview.

## 2. Review post (step "post text") → `RUN/note/review-post.md`
The `:eyes:` review line from the template, a blank line, then the full note.
Also write `RUN/note/mentions.txt`: every person/group to @mention, one per line, exactly as Slack shows them
(e.g. `Sayeed (HighLevel)`, `memberships-team`).

## 3. Form handoff (step "form") → `RUN/note/form-handoff.md`
Every Release Update Form field in order (see the template), each value in its own code block; "Describe the release"
holds the full note. Then the upload list: `RUN/shots/final/*.png` in order with a one-line alt text each, then the video.

## 4. Lint (step "lint")
`python3 -I KIT/scripts/qa.py RUN --note-only` until it reports no ERROR. Fix the copy, never the checker.

## Report back (≤ 12 lines)
The headline, the "What's New" titles, the mention list, and anything the brief didn't settle (unknown designer,
missing links). Mark `run.py session RUN note done`.

## Change requests after checkpoint B
You may be resumed with an edit. Change only what was asked, keep the format, re-run the lint, report the diff in a
few lines.
