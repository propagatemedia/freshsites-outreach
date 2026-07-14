# FreshSites — Pre-Launch Checklist

## Before you send ANY real outreach

### 1. Web3Forms key (REQUIRED for contact forms + delete notifications)
The contact form and the "Not for me" delete-notification both POST to Web3Forms.
Right now the demos contain the placeholder `YOUR_WEB3FORMS_KEY` and will NOT work until you set a real key.

Steps:
1. Go to https://web3forms.com — enter the email you want submissions sent to
   (e.g. freshsites@sites.propagate.media or tyrone@propagate.media).
2. They email you an Access Key instantly (no account needed).
3. Put it in `.env`:  `WEB3FORMS_KEY=<the-key>`
4. Rebuild all demos:  `for s in $(ls extracted/*.json | xargs -n1 basename | sed 's/.json//'); do python3 agents/generate_demos_v3.py $s; done`
5. Commit + push.

Result: every contact-form submission AND every "Not for me" click emails you.

### 2. Stripe — client tracking (DONE in code)
Each demo's Buy buttons now carry `?client_reference_id=<slug>`.
When a payment lands, open the Stripe payment in the dashboard — the `client_reference_id`
field tells you exactly which garage/demo bought. Wire a Stripe webhook later to automate.

### 3. DMARC (DNS — you or your mail host must do this)
Current: `_dmarc.propagate.media  ->  v=DMARC1; p=none; aspf=r; adkim=r;`
`p=none` = monitor only, no spoof protection. Fine for warmup.
When ready to harden, change the DNS TXT record to:
   `v=DMARC1; p=quarantine; rua=mailto:dmarc@propagate.media; aspf=r; adkim=r;`
This is a DNS change at your domain registrar / mail host — cannot be done from the repo.
SPF and DKIM already pass, so deliverability is otherwise good.

### 4. Email warmup
sites.propagate.media is a relatively fresh sending subdomain.
Ramp cold sends slowly: ~5-10/day week 1, doubling weekly. Sending 50 cold on day 1
risks the subdomain reputation.

### 5. Delete is MANUAL (by design for v1)
"Not for me" does NOT delete the file. It:
  - emails you a DELETE REQUEST with the slug + live URL
  - tells the prospect "removed within 12 hours"
You then delete the file manually:
   `git rm docs/demos/<slug>.html demos/<slug>.html && git commit -m "Remove declined demo <slug>" && git push`

## Notes
- Score shown in the EMAIL is the WEBSITE score, not the business. Wording clarified.
- Demos do NOT show any score. Clean.
- .env is gitignored. leads/freshsites.db is now gitignored (was tracked before — see history note).
