# Interview (only the gaps)

Ask after reading ClickUp + PRs. Pre-select the answer the facts point to and mark it "(Recommended)". Two
`AskUserQuestion` rounds at most; skip any question the facts already answer. Drafted text (headline, why it matters,
how to get started, thanks) is **not** asked here: it is shown for edits at checkpoint A.

## Round 1
| Header | Question | Options (multiSelect) |
|---|---|---|
| Type | Which release type is this? | T1 New Product · T2 New Feature · T3 Enhancements · T4 Internal Release / Bug Fixes |
| Label | How should it be announced? | Announce · Do not Announce · LevelUp Release - Do not Announce |
| Surfaces | Where does the change show up? (multi) | Builder (web) · Public event page · Client Portal (web) · Mobile app |
| Video | Make a narrated video for this release? | Yes (Recommended) · No |

## Round 2
| Header | Question | Options |
|---|---|---|
| Access | Who gets it? | Everyone · Behind a feature flag (name it) · Specific plans (which) |
| i18n | Is it translation-ready? | Yes · No · Not applicable |
| Design | Did it go through design review? | Yes (name the designer) · No |
| CC | Default CC is @svr- @Shivam @Ashutosh Anand @Jitesh Arora @memberships-team. Any other team? | Default only · Add teams |

## Free text (one chat line, only if missing)
- ClickUp and PR links (asked in preflight).
- Change log, support doc, public API links (default "NA").
- Ideas Board vote count (optional).

## Surfaces from the facts
Use the PR's repo, changed paths and the ClickUp text to pre-select surfaces; the author confirms.

| Signal | Surface |
|---|---|
| Events builder screens, `memberships/events`, event settings, Attendee App tab | Builder (web) |
| Public event page, checkout, registration, `preview`, embed | Public event page |
| Client Portal web, member portal, `clientclub` | Client Portal (web) |
| Flutter / `.dart`, mobile app, push notifications in the app | Mobile app |
| Backend only (`events-management`, workers) | ask which screen shows the effect |

## Brief fields (brief.md → Interview)
Product heading · Owner · Team (Revex) · Product (Events) · ClickUp link(s) · Release Type · Label · Surfaces · Video ·
Why it matters · How to get started · Availability · Special thanks · CC · i18n · Change log / Support doc / Public API ·
Ideas Board votes · Design review · Designer.
