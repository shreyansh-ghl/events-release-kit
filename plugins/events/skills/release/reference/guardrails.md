# Guardrails (each one was learned the hard way)

## Content
- **Real UI only.** Screens are captured from the live product. Never redraw product UI, never add a button, badge,
  stat or panel the product doesn't have. If a step has no screen, say it in the narration only.
- **Fictional data only.** Everything visible comes from the Northstar world (`northstar/world.json`): Northstar
  Collective, Northstar Summit, Maya Okafor and co., Brightwave CRM and the other exhibitors, DiceBear avatars.
  No real people, colleagues, customers, brands or ads. No staging junk ("Test Internal Event", "TTTTTTT", "sachin").
  Exception: a "real-world proof" card (e.g. "Powering LevelUp") only when the author asks for it explicitly.
- **Claims:** describe what the product does, not what it might do. No "automatically" unless it is automatic.
- **Names:** the product line is "Events"; say the feature as "Events'" + its real name ("Events' coupon codes").

## Tone and look
- Professional, warm, confident. Personality comes from rhythm and contrast, never jokes or gags.
- House look only (`tokens.json`): warm paper and ink, Instrument Serif headlines with one italic phrase, Inter, Geist
  labels. No purple glows, no gradient text, no generic "AI" look.

## Safety while capturing
- **Outside Northstar: read-only.** Open dialogs to look, then Cancel. Never Save, Publish, Delete, Send, Switch account.
- **Inside Northstar:** create or edit only what this feature needs, after the author says yes, and record it in
  `northstar/world.json`.
- Never press Escape inside builder modals (it can close the whole dialog); use the dialog's Cancel.
- Page zoom shortcuts don't work through the extension; use the `zoom` action.
- Hide staging-only overlays (dev tool bars) with in-page CSS; that is display-only, never a save.

## People and accounts
- The author types every password and verification code; Claude never does.
- Never read, cat or print credential files (`.npmrc`, `.mcp.json`, `.env`); show key names only.
- Post only from the author's own Slack session after they say "post it". Never as a bot, never to another channel.
- The Release Update Form is the author's: Claude never opens or submits it.

## Limits
- One release note per thing shipped.
- A post holds at most 10 attachments: **≤ 9 images + 1 video**. The video must be < 100 MB (the renderer re-encodes).
- Exactly two checkpoints (A after capture, B on the final pack).
