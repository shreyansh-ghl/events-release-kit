# Release note: team format

Slack text (the composer renders `*bold*`, `` `code` ``, emoji shortcodes and `•` bullets; it does **not** render
`**bold**` or `#` headings). Write mentions as plain `@Full Name (HighLevel)`; the post step turns each into a real
mention from Slack's dropdown and also needs them listed in `note/mentions.txt`. See `note-examples.md` for two real posts.

```text
-----------------------------------------------------------------------------------------------------------------------------------------------------
           :gohighlevel: <Headline: "Introducing Events' <Feature>: <benefit>" or "<Feature> is Here! <benefit>">  :gohighlevel:
-----------------------------------------------------------------------------------------------------------------------------------------------------

Owner: @<author> (HighLevel)
Team: 
Revex
Product: Events
Clickup Link: <links joined with " | ">
------------------------------------------------------------------------------------------

Release Type: 
<T1 - New Product | T2 - New Feature | T3 - Enhancements | T4 - Internal Release / Bug Fixes>

Label: 
<Announce | Do not Announce | LevelUp Release - Do not Announce>

Overview:
<2–4 short paragraphs: the old pain in one line → what's new → where it lives / rollout.>

:sparkles: What's New?

:<emoji>: <Sub-feature title in Title Case>
<1–3 sentences, or "* " bullets. Prefix brand-new triggers/actions with `NEW`.>

(repeat per sub-feature; 2–9 of them; one blank line between)

:bulb: Why This Matters
• For attendees: ...
• For organizers: ...
• For exhibitors and sponsors: ...      (only roles that apply)

:rocket: How to Get Started            (or ":bulb: Automations You Can Build" with "A → B → C" lines)
1. Go to Events → select an event → <tab>.
2. ...

<One-line closer with rhythm, e.g. "One platform. Every attendee. A more connected event experience.">

:heart: Special Thanks & Shoutouts
<who did what, one line per role (two people sharing a role may share a line), @mentions; from the facts, edited by the author>

CC :  @svr- @Shivam (HighLevel) @Ashutosh Anand (HighLevel) @Jitesh Arora (HighLevel) @memberships-team <extra teams>

i18n ready?: <Yes | No | Not Applicable>

:paperclip: Change log Link: <link | NA>
:books: Support Doc: <link | NA>
:link: Public API : <link | NA>

Did it go through design review?: <Yes | No>

Designer name :<@Designer (HighLevel) | NA>
```

## Writing rules
- Benefit first, plain words, short sentences. Professional and warm; one exclamation at most per section.
- Every claim must come from the brief (ClickUp, PRs, interview). Nothing the product doesn't do.
- Sub-feature emoji: pick a fitting Slack shortcode (`:admission_tickets:` `:date:` `:handshake:` `:briefcase:`
  `:mega:` `:bell:` `:art:` `:compass:` `:zap:` …); never repeat one in the same note.
- Paths in "How to Get Started" follow the captured screens exactly (e.g. "Memberships" → "Events" → event → "Attendee App"), real labels in quotes, `→` between steps.
- One blank line between blocks (the extra gaps in the examples are paste artifacts).
- Mentions are search keys: `@Name (HighLevel)`. The post step picks the exact person from Slack's dropdown, so spelling
  of the suffix doesn't matter; `mentions.txt` lists every person and group mentioned, owner and CC groups included.
- Product name: "Events" and "Events' <Feature>". Northstar is only for screenshots, never in the note text.

## Review post (`note/review-post.md`)
First line: `:eyes: Release note for review: <headline without its final period>. <"Video and screenshots" | "Screenshots" | "Screenshot"> attached; approve with :white_check_mark: or reply in thread.` (match what is actually attached)
Then a blank line, then the full note above.

## Form handoff (`note/form-handoff.md`)
Every Release Update Form field in form order, each value in its own code block so it copies cleanly:
Product heading · Owner · Team · Product · ClickUp link · Release Type · Label · Describe the release (the full note)
· i18n · Change log · Support doc · Public API · Ideas Board votes · Design review · Designer.
Then the upload list: images in post order (file name + one-line alt text) and the video.
A field the brief doesn't settle gets `NA (author: please fill)`; list it in your report.
Form steps 2–5 are not mapped yet: end with "Later form steps: fill from the fields above; tell the kit owner what was
asked so it can be added here."
