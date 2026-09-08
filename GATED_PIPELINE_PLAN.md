# FreshSites Outreach Pipeline — Gated QA Plan

Every lead moves through this pipeline in strict order. No stage can be
skipped. Nothing sends without the Final Gate = GREEN from Tyrone.

## STAGE 0 — Discovery & Triage
Google Maps scrape. For each business:
- No website + phone → SMS list
- Social-only + phone → SMS list
- No website, no phone → SKIP
- Has website → Stage 1

## STAGE 1 — Hydrate & Screenshot
- Load the real site in a real browser, wait for full hydration
- Screenshot it
- Score it: speed, mobile, design, CTA clarity, broken links

## GATE 1 — Candidate QA (two independent subagents)
- Agent A and Agent B each independently review the screenshot + score
- Verdict: genuine rebuild candidate vs reject
- National/established brands auto-reject
- Both must agree to PASS. Any disagreement = auto-reject, logged for
  human review

## STAGE 2 — Build Demo (only if Gate 1 = PASS)
- Extract real brand data: name, services, phone, real imagery
- Build demo HTML with real content, no filler/placeholder

## GATE 2 — Build QA (fresh subagent)
- Screenshots the BUILT demo
- Checks: matches the real business, no lorem/placeholder junk,
  looks professional, on-brand
- PASS/FAIL + written notes logged

## GATE 3 — Link & Function Check (only if Gate 2 = PASS)
- HTTP 200 on live URL
- All internal links resolve
- tel: links valid
- CTA buttons work
- Pricing renders
- Contact form present

## STAGE 3 — Compose Email (only if Gate 3 = PASS)
- Personalized to the business
- Correct demo link, correct price

## GATE 4 — Email Content QA
- Subagent checks: correct name/link, no typos, no template leftovers,
  tone matches brief, link actually clicks through

## FINAL GATE — Human Green Light (Tyrone)
- Nothing sends without explicit per-batch approval
- You see: business name, score, screenshot, demo link, email draft —
  all in one view — before any send is scheduled

## STAGE 4 — Scheduled Send (only if Final Gate = GREEN)
- One at a time
- Weekday only, office hours only (9am–5pm Mon–Fri)
- Staggered gaps, 10 min minimum, never batch-blasted

## STAGE 5 — Lifecycle
- Day 5 (next weekday, office hours): auto follow-up if no reply
- Day 10: check mailbox for replies → mark engaged
- Day 15: if no reply/not engaged → delete demo from git, archive lead

## Logging
Every gate writes: timestamp, agent(s) involved, verdict, notes,
screenshot path. Nothing skips a gate. Nothing sends without Final
Gate = GREEN.
