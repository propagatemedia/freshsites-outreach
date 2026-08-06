# FreshSites Multi-Reviewer Qualification Gate

Use this before building or sending demos for any borderline candidate.

The goal is accuracy, not filling quota. A candidate must be commercially weak, not merely ugly.

## Roles

### 1. Conversion reviewer
Bias: protect against false positives where the existing site already converts.

Check and record:
- phone visible above fold
- sticky call/email/book header
- email visible
- online booking, payment, quote or contact action
- contact form
- repeated call-to-action after hero
- clickability of tel/mailto links where visible

Output:
```json
{
  "role": "conversion",
  "score_35": 0,
  "assets": [],
  "major_risks": [],
  "send_ok": false,
  "reason": ""
}
```

### 2. Trust reviewer
Bias: protect against targeting credible businesses whose site is commercially adequate.

Check and record:
- reviews/testimonials visible or linked
- Google/Checkatrade/Yell/Trustatrader proof
- real photos, vans, team, jobs, equipment
- address, service area, trading identity
- years established, guarantees, accreditations, licences
- social links that prove activity

Output:
```json
{
  "role": "trust",
  "score_25": 0,
  "assets": [],
  "major_risks": [],
  "send_ok": false,
  "reason": ""
}
```

### 3. Design/service reviewer
Bias: design matters, but do not confuse taste with weakness.

Check and record:
- first impression and visual hierarchy
- broken sections, blank areas, mobile/layout problems
- service cards/pages and coverage areas
- emergency vs routine routes
- FAQ/guidance content
- clarity of what they actually do

Output:
```json
{
  "role": "design_service",
  "score_40": 0,
  "assets": [],
  "major_risks": [],
  "send_ok": false,
  "reason": ""
}
```

## Arbiter review

The arbiter reconciles reviewers and makes the only final call.

Must answer:
1. What already works on the current site?
2. What is genuinely broken or commercially weak?
3. Is the weakness serious enough that a cold email feels fair?
4. Does the demo fix that specific weakness?
5. Would Tyrone be embarrassed if the owner replied, "our site already has all of that"?

Output:
```json
{
  "candidate_score_100": 0,
  "conversion_assets": [],
  "trust_assets": [],
  "service_assets": [],
  "reviewers": [],
  "arbiter": {
    "what_already_works": [],
    "genuine_weaknesses": [],
    "owner_fairness_check": "",
    "demo_specific_improvement": "",
    "send_ok": false,
    "reason": ""
  }
}
```

## Mechanical decision rules

Block outreach if any of these are true:

- fewer than 2 of 3 reviewers say `send_ok=true`
- arbiter says `send_ok=false`
- candidate score is 50+ and there is no severe defect override
- current site has 4+ conversion assets and 3+ trust/service assets
- no verified public email
- demo is not clearly better on the exact weakness

## Severe defect override

Only use when a defect meaningfully damages trust/action.

Allowed examples:
- page appears broken/blank to normal visitors
- form or booking flow visibly fails
- phone/email buried or unclickable on mobile
- core service is unclear despite being a service business

Not enough by itself:
- ugly colour palette
- old Wix/Squarespace look
- cluttered nav
- chat widget
- too much SEO copy
- random CTAs when the main call/book/form routes still exist

## Quick Drains example

Quick Drains would trigger review because of large blank purple sections. But reviewers must also notice:
- phone visible above fold
- sticky top actions
- email visible
- book online
- pay online
- reviews section
- areas covered
- service cards/pages
- Checkatrade/Trustatrader/Yell references

That asset density means it is not an automatic FreshSites candidate. It should be blocked unless the arbiter proves the blank sections are visible to normal users and materially damage enquiry flow enough to outweigh the existing conversion infrastructure.
