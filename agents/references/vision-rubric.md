# FreshSites Vision Review Rubric

The vision review agent looks at TWO full-page screenshots — the prospect's CURRENT
live website and the FreshSites DEMO — and judges them like a real small-business owner
and a conversion expert would. This replaces keyword-counting with actual visual judgment.

The agent MUST look at the images. It does not infer from HTML. It scores what a human sees.

## How to run a review

1. Capture screenshots:
   `PYTHONPATH="" ./.venv/bin/python3.11 agents/vision_capture.py <slug> <prospect_url> <demo_url>`
   (writes review/<slug>/prospect.png and review/<slug>/demo.png)
2. Load BOTH images (vision_analyze / browser_vision).
3. Score each screenshot against the rubric below.
4. Write review/<slug>/verdict.json in the exact schema at the bottom.
5. gate_check.py reads the verdict and passes/blocks outreach.

## Scoring dimensions (score EACH site 0-10 on each)

### 1. First impression / visual design (weight 35%)
- Does it look modern and professional, or dated and amateur?
- Whitespace, typography, colour harmony, image quality.
- 0-3: looks broken/1990s/clip-art. 4-6: dated but functional. 7-8: clean, current. 9-10: genuinely impressive.
- A real owner's gut reaction: "would I be proud to hand this card to a customer?"

### 2. Trust & credibility (weight 20%)
- Reviews/testimonials visible? Real photos (not stock-obvious)? Established/years badge?
- Clear it's a REAL local business, not a template shell?
- Broken images, lorem ipsum, placeholder text = trust killers, score low.

### 3. Conversion clarity (weight 30%)
- Is the ONE thing they want you to do obvious within 3 seconds (call / book)?
- Phone clickable and prominent? Clear CTA button above the fold? Contact form present and usable?
- Confusing nav, buried phone, no CTA = low. Instant "tap to call / book now" = high.

### 4. Mobile impression (weight 15%)
- From the screenshot proportions and layout, does it look like it would work on a phone?
- Tiny text, fixed-width desktop layout, horizontal scroll = low.

## The comparison verdict (THIS is the gate)

After scoring both, answer plainly:
- **is_demo_better**: true ONLY if the demo is clearly, visibly a step up a real owner would notice.
- **improvement**: demo_overall - prospect_overall (must be >= +2.0 to pass the gate).
- **honest_call**: one sentence a human would say, e.g. "Their site is a dated single-page
  with no reviews and a buried number; the demo is cleaner, phone is tap-to-call up top, and
  it has services + a form — genuinely better." OR "Their existing site is actually solid
  (7/10) — do NOT send, we can't credibly claim to improve it."

## Hard honesty rules (non-negotiable — Tyrone's standard)
- If the prospect site scores >= 6.5 overall, RECOMMEND SKIP. We cannot credibly cold-email
  someone with a decent site claiming we'll improve it. Set send_ok=false.
- Never inflate the prospect's flaws to justify outreach. If it's fine, say it's fine.
- Never claim the demo fixes something the prospect site already does well.
- The score is of the WEBSITE, not the business. Say so if it ever leaks into copy.
- If EITHER screenshot failed to capture (blank/error page), set send_ok=false and flag it —
  never review a page you couldn't see.

## verdict.json schema (write EXACTLY this shape)
```json
{
  "slug": "www-graiggochgarage-co-uk",
  "prospect": { "design": 3, "trust": 2, "conversion": 3, "mobile": 4, "overall": 3.0,
                "notes": "Dated single page, no reviews, phone not clickable, thin content." },
  "demo":     { "design": 8, "trust": 6, "conversion": 9, "mobile": 8, "overall": 7.9,
                "notes": "Clean hero, tap-to-call, 6 services with images, form, map, trust bar." },
  "is_demo_better": true,
  "improvement": 4.9,
  "honest_call": "Their site is a dated one-pager with a buried number; the demo is a clear, credible step up.",
  "send_ok": true,
  "captured_ok": true
}
```

The email/outreach step must refuse to send when send_ok=false.
