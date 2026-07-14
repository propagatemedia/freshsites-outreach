# FreshSites — Pre-Launch Checklist

## Before you send ANY real outreach

### 1. FormSubmit activation (REQUIRED — one-time, free, no key)
The contact form and the "Not for me" delete-notification both POST to FormSubmit.co
(free, unlimited, no signup, no API key). Submissions email: freshsites@sites.propagate.media

ONE-TIME ACTIVATION (per email address, ever):
1. Open any live demo and submit the contact form once (or the "Not for me" button).
2. FormSubmit sends a one-time confirmation email to freshsites@sites.propagate.media.
3. Click the activation link in that email.
4. Done forever — every future submission from ANY demo emails you, unlimited, free.

To change the destination email, edit FORM_EMAIL in `.env` and rebuild:
   `for s in $(ls extracted/*.json | xargs -n1 basename | sed 's/.json//'); do python3 agents/generate_demos_v3.py $s; done`

OPTIONAL (hide your email from page source): after activation, FormSubmit gives you a
random alias (e.g. formsubmit.co/ajax/abc123def). Put that alias in FORM_EMAIL instead
of the raw address and rebuild. Not required for launch.

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
