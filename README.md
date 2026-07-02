# FreshSites Outreach System

**Automated sales funnel for local businesses with weak websites.**

> Powys, Wales · Automotive trades · Buy-outright £149 · freshsites@sites.propagate.media

---

## How It Works

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  1. DISCOVER    │───→│  2. SCORE       │───→│  3. BUILD DEMO  │───→│  4. EMAIL       │
│  Search + Audit │    │  0-10 rubric    │    │  Landing page   │    │  Outreach       │
│  Find leads     │    │  Flag < 7       │    │  Brand-matched  │    │  Demo link      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                                            │
                                                                            ▼
                                                                   ┌─────────────────┐
                                                                   │  5. CONVERT     │
                                                                   │  Stripe buy     │
                                                                   │  £149 outright  │
                                                                   └─────────────────┘
                                                                            │
                                                                            ▼
                                                                   ┌─────────────────┐
                                                                   │  6. DELIVER     │
                                                                   │  Zip + README   │
                                                                   │  Hosting guide  │
                                                                   └─────────────────┘
```

---

## Current Status

| Business | Score | Status | Demo |
|---|---|---|---|
| **Welshpool Autofit** | 3.3/10 | `demo_built` | [Live Demo](https://propagatemedia.github.io/freshsites-outreach/demos/welshpool-autofit.html) |
| **Blakemore's Autos** | 6.7/10 | `demo_built` | [Live Demo](https://propagatemedia.github.io/freshsites-outreach/demos/blakemores-autos.html) |
| **William Nunns** | 6.7/10 | `demo_built` | [Live Demo](https://propagatemedia.github.io/freshsites-outreach/demos/william-nunns.html) |
| Brecon Motors | 7.1/10 | `new` | — |
| BTS The Garage Adfa | 7.5/10 | `new` | — |
| Car and Van Welshpool | 7.5/10 | `new` | — |
| DC Auto Repairs | 7.9/10 | `new` | — |
| K's Garage | 7.9/10 | `new` | — |
| Bradleys Garage | 8.3/10 | `new` | — |
| Ian Jones Tyres | 8.3/10 | `new` | — |
| Border Garage | 8.8/10 | `new` | — |
| Grooms Garage | 9.2/10 | `new` | — |
| Newtown Tyres | 9.6/10 | `new` | — |
| Jacks Tyres | 9.6/10 | `new` | — |

**3 qualified leads identified, 3 demo pages built and deployed.**

---

## Project Structure

```
freshsites-outreach/
├── agents/
│   ├── discover.py      # Business discovery + website scoring
│   ├── emailer.py       # Email outreach with Himalaya
│   └── deliver.py       # Post-purchase zip + hosting guide
├── demos/
│   ├── welshpool-autofit.html
│   ├── blakemores-autos.html
│   └── william-nunns.html
├── leads/
│   └── freshsites.db    # SQLite lead database
├── templates/
│   └── [email templates]
├── scripts/
│   └── [automation scripts]
└── docs/                # GitHub Pages deployment
    └── index.html       # Root page
    └── demos/           # Demo pages
```

---

## Scoring Rubric (0-10)

| Metric | Weight | Max |
|---|---|---|
| Mobile responsive | 1.0 | 1 |
| CTA present | 1.5 | 2 |
| Phone visible | 0.5 | 1 |
| Social proof | 1.0 | 1 |
| Title quality | 0.5 | 2 |
| H1 present | 1.0 | 2 |
| Contact form | 1.0 | 1 |
| Social links | 0.5 | 1 |
| Images | 0.5 | 2 |
| Meta description | 0.5 | 1 |
| Clean URLs | 0.5 | 1 |

**Threshold:** Score < 7.0 = qualified for outreach

---

## Running the Pipeline

### 1. Discover + Score

```bash
cd ~/git/freshsites-outreach
PYTHONPATH="" ./.venv/bin/python3.11 agents/discover.py
```

### 2. Build Demos

Currently manual (one page per lead). Future: automated builder agent.

### 3. Deploy

```bash
# GitHub Pages (auto on push)
git add -A && git commit -m "Update demos" && git push origin main
```

### 4. Email Outreach

Preview mode (safe):
```bash
PYTHONPATH="" ./.venv/bin/python3.11 agents/emailer.py
```

Send mode (actually dispatches):
```bash
PYTHONPATH="" ./.venv/bin/python3.11 agents/emailer.py --send
```

Requires Himalaya CLI configured with `gravityaddiction` account.

### 5. Post-Purchase Delivery

```bash
PYTHONPATH="" ./.venv/bin/python3.11 agents/deliver.py <lead_id>
```

Generates:
- `index.html` (the page)
- `README.md` (hosting instructions)
- ZIP package for email attachment

---

## Email Sequence

| Day | Email | Subject |
|---|---|---|
| 0 | Initial | "I built [Business] a better homepage" |
| 3 | Follow-up | "Re: [Business] homepage — still interested?" |
| 7 | Scarcity | "3 spots this month" |
| 14 | Breakup | "Last chance — demo coming down" |

---

## Pricing Model

| Tier | Price | Includes |
|---|---|---|
| **Buy Outright** | £149 | Single landing page, HTML/CSS, self-hosted |
| **Custom Tweaks** | £50-150 | Logo swap, extra sections, color changes |
| **Multi-page** | £299+ | Home + 2-3 pages, full micro-site |
| **Managed Hosting** | £15/mo | We host, maintain, update |

---

## Buy Button Integration

The demo pages include a fixed bottom bar with:
- **"Buy This Page — £149"** → Stripe Checkout link (placeholder)
- **"Request Custom Changes"** → Mailto to freshsites@sites.propagate.media

Replace the Stripe test link with your real checkout URL:
```html
<a href="https://buy.stripe.com/YOUR_REAL_LINK" class="btn-primary">Buy This Page — £149</a>
```

---

## To-Do

- [x] Discovery agent with scoring
- [x] SQLite lead database
- [x] 3 demo pages built and deployed
- [x] Emailer agent with preview/send modes
- [x] Delivery agent (zip + README)
- [ ] Automated demo builder (from lead data)
- [ ] Real Stripe checkout integration
- [ ] Cron job for weekly discovery runs
- [ ] Follow-up email automation (3, 7, 14 day sequence)
- [ ] Expand to other verticals (trades, hospitality, professional services)
- [ ] Add Google Maps API for richer business discovery
- [ ] Browser screenshot capture for visual comparison

---

## Brand

**FreshSites by Propagate Media**
- Email: freshsites@sites.propagate.media
- Deployed on: GitHub Pages
- Target: Powys, Wales (automotive trades)

---
