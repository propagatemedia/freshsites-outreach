#!/usr/bin/env python3
"""FreshSites trade demo generator.

Purpose-built for non-garage trade leads where the original site is dead, blank,
suspended, under construction, or missing. Reads extracted/<slug>.json and writes:
- demos/<slug>.html
- docs/demos/<slug>.html
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXTRACTED = REPO / "extracted"
DEMOS = REPO / "demos"
DOCS_DEMOS = REPO / "docs" / "demos"
DEMOS.mkdir(exist_ok=True)
DOCS_DEMOS.mkdir(exist_ok=True, parents=True)
IMG_BASE = "../assets/img/"
FORM_EMAIL = "freshsites@sites.propagate.media"
SCHEDULE_CALL_URL = "https://propagate.media/schedule-call"
BUY_OUTRIGHT_URL = "https://buy.stripe.com/14AaENc4oeYBgfk26R5EY0f"
HOSTED_URL = "https://buy.stripe.com/fZu4gpecw2bPbZ4dPz5EY0g"

VERTICALS = {
    "electrician": {
        "label": "Electrical services",
        "hero": "Fast, safe electrical work without making customers hunt for the phone number.",
        "services": ["Emergency call-outs", "Consumer unit upgrades", "Rewires and fault finding", "Testing and certification", "Commercial electrical work", "EV charger installation"],
        "proof": ["Qualified credentials", "Clear call-out areas", "Tap-to-call on mobile", "Quote request form"],
        "accent": "#f5b301",
        "image": "trade-electrician.jpg",
    },
    "roofing": {
        "label": "Roofing services",
        "hero": "A cleaner roofing site that turns storm damage, leaks and quote requests into calls.",
        "services": ["Roof repairs", "Flat roofing", "Leadwork", "Moss removal", "Emergency leak response", "New roofs and replacements"],
        "proof": ["Before/after gallery", "Local coverage", "Emergency CTA", "Quote request form"],
        "accent": "#334155",
        "image": "trade-roofing.jpg",
    },
    "plumbing": {
        "label": "Plumbing and heating",
        "hero": "A practical plumbing site built around urgent calls, quotes and trust signals.",
        "services": ["Emergency plumbing", "Boiler servicing", "Heating repairs", "Bathroom installs", "Leak detection", "Landlord checks"],
        "proof": ["Tap-to-call CTA", "Service area clarity", "Simple request form", "Trust badges"],
        "accent": "#0e7490",
        "image": "trade-plumbing-supplies.jpg",
    },
    "construction": {
        "label": "Construction services",
        "hero": "A sharp construction site that makes capabilities, proof and enquiries obvious.",
        "services": ["Cladding", "Roofing", "Maintenance", "Commercial projects", "Repairs", "Project enquiries"],
        "proof": ["Project gallery", "Accreditations", "Clear sectors served", "Enquiry form"],
        "accent": "#b45309",
        "image": "trade-cladding.jpg",
    },
    "supply": {
        "label": "Trade supplies",
        "hero": "A working local supplier page with stock categories, directions and call-to-order routes.",
        "services": ["Plumbing supplies", "Heating parts", "Trade counter", "Local delivery", "Advice and ordering", "Brands stocked"],
        "proof": ["Opening hours", "Clickable directions", "Call-to-order CTA", "Product categories"],
        "accent": "#0f766e",
        "image": "trade-plumbing-supplies.jpg",
    },
}


def esc(x):
    return html.escape(str(x or ""), quote=True)


def slugify(name: str) -> str:
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", name.lower()))


def vertical_key(data: dict) -> str:
    text = " ".join(str(data.get(k, "")) for k in ["industry", "vertical", "name", "category"]).lower()
    if any(k in text for k in ["electric", "electrical"]):
        return "electrician"
    if any(k in text for k in ["roof", "leadwork"]):
        return "roofing"
    if any(k in text for k in ["supply", "supplies", "store"]):
        return "supply"
    if any(k in text for k in ["plumb", "heating", "boiler", "hvac"]):
        return "plumbing"
    if any(k in text for k in ["clad", "construction", "builder", "carpenter"]):
        return "construction"
    return "construction"


def clean_phone(phone: str) -> str:
    return re.sub(r"[^+0-9]", "", phone or "")


def stripe_url(base: str, slug: str) -> str:
    return f"{base}?client_reference_id={esc(slug)}"


def service_cards(services):
    icons = ["⚡", "🛠", "📋", "📍", "☎", "✓"]
    out = []
    for i, svc in enumerate(services[:6]):
        out.append(f"""
        <article class="service-card">
          <div class="svc-icon">{icons[i % len(icons)]}</div>
          <h3>{esc(svc)}</h3>
          <p>Clear, plain-English service information with a direct route to request a quote or call the team.</p>
        </article>""")
    return "\n".join(out)


def generate(data: dict) -> str:
    key = vertical_key(data)
    v = VERTICALS[key]
    name = data.get("name", "Local Business")
    if not name or name.strip() == "" or name == "Local Business":
        raise ValueError(
            f"REFUSED TO BUILD: extracted data has no real business name "
            f"(slug={data.get('slug')!r}). This is the exact bug that produced "
            f"placeholder demos before (Callum McKay Slaters, Ross of Rutherglen, "
            f"SM Plumbing). Fix the extraction JSON's 'name' field before building."
        )
    slug = data.get("slug") or slugify(name)
    phone = data.get("phone", "")
    tel = clean_phone(phone)
    if not tel:
        raise ValueError(
            f"REFUSED TO BUILD: extracted data has no phone number for {name!r} "
            f"(slug={slug!r}). A demo with no working tel: link is useless - "
            f"fix the extraction JSON's 'phone' field before building."
        )
    email = data.get("email") or data.get("contact_email") or ""
    location = data.get("location") or data.get("address") or ""
    services = data.get("services") or v["services"]
    brand = data.get("brand_color") or v["accent"]
    reason = data.get("audit_summary") or "The current web presence is either missing, broken, blank, or too thin to convert search traffic reliably."
    original_url = data.get("website") or data.get("source_url") or ""
    form_email = data.get("form_email") or FORM_EMAIL
    map_q = re.sub(r"\s+", "+", location or name)
    img = IMG_BASE + (data.get("hero_image") or v["image"])
    proof = "".join(f"<li>{esc(x)}</li>" for x in v["proof"])
    email_html = f"<p><strong>Email:</strong> <a href='mailto:{esc(email)}'>{esc(email)}</a></p>" if email else ""
    phone_html = f"<a class='btn primary' href='tel:{esc(tel)}'>Call {esc(phone or 'Now')}</a>" if phone else "<a class='btn primary' href='#contact'>Request a Quote</a>"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(name)} | {esc(v['label'])}</title>
<style>
:root {{--brand:{brand};--dark:#101318;--ink:#14171f;--muted:#667085;--line:#e7e9ee;--bg:#f6f7f9;--card:#fff}}
* {{box-sizing:border-box}}
html {{scroll-behavior:smooth}}
body {{margin:0;font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;color:var(--ink);background:var(--bg);line-height:1.6;padding-bottom:82px}}
a {{color:inherit;text-decoration:none}}
.wrap {{max-width:1120px;margin:0 auto;padding:0 22px}}
.top {{background:var(--dark);color:#fff;font-size:.92rem}}
.top .wrap {{display:flex;justify-content:space-between;gap:16px;padding-top:10px;padding-bottom:10px;flex-wrap:wrap}}
header {{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:50}}
nav {{display:flex;align-items:center;justify-content:space-between;padding:18px 0;gap:22px}}
.brand {{font-weight:900;font-size:1.2rem;letter-spacing:-.03em}}
.links {{display:flex;align-items:center;gap:24px;font-weight:750}}
.btn {{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;padding:12px 20px;font-weight:850;border:2px solid var(--brand);cursor:pointer;color:#fff !important;background:var(--brand);box-shadow:0 10px 24px rgba(0,0,0,.12)}}
.btn.secondary {{background:#fff;color:var(--brand)!important}}
.hero {{position:relative;min-height:620px;color:#fff;overflow:hidden;background:var(--dark)}}
.hero img {{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center;filter:saturate(.94)}}
.hero:after {{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(16,19,24,.9),rgba(16,19,24,.72) 48%,rgba(16,19,24,.22))}}
.hero-in {{position:relative;z-index:1;min-height:620px;display:flex;align-items:center;text-align:left}}
.hero-in > div {{text-align:left;max-width:640px}}
.eyebrow {{display:block;color:var(--brand);text-transform:uppercase;letter-spacing:.16em;font-size:.78rem;font-weight:950;text-align:left}}
h1 {{font-size:clamp(2.35rem,6vw,5rem);line-height:.98;margin:12px 0 18px;letter-spacing:-.06em;text-align:left}}
.lead {{font-size:1.22rem;color:#e5e7eb;max-width:680px;text-align:left}}
.hero-actions {{display:flex;gap:14px;margin-top:28px;flex-wrap:wrap;justify-content:flex-start}}
.section {{padding:102px 0 82px}}
.section[id] {{scroll-margin-top:92px}}
.grid {{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}}
.service-card,.audit-card,.contact-card {{background:#fff;border:1px solid var(--line);border-radius:22px;padding:26px;box-shadow:0 14px 34px rgba(15,23,42,.07)}}
.service-card {{transition:.2s transform,.2s box-shadow}}
.service-card:hover {{transform:translateY(-4px);box-shadow:0 20px 45px rgba(15,23,42,.12)}}
.svc-icon {{width:54px;height:54px;border-radius:16px;background:color-mix(in srgb,var(--brand) 14%,#fff);display:flex;align-items:center;justify-content:center;font-size:1.5rem;margin-bottom:16px}}
h2 {{font-size:clamp(2rem,4vw,3rem);letter-spacing:-.04em;line-height:1.08;margin:8px 0 14px}}
h3 {{margin:0 0 8px;font-size:1.18rem}}
p {{margin:0 0 14px}}
.split {{display:grid;grid-template-columns:1fr 1fr;gap:36px;align-items:center}}
.audit-card {{background:var(--dark);color:#fff}}
.audit-card p,.audit-card li {{color:#d7dce5}}
.contact {{background:#fff}}
.contact-grid {{display:grid;grid-template-columns:1.1fr .9fr;gap:28px}}
label {{display:block;font-weight:800;margin-bottom:6px}}
input,textarea,select {{width:100%;border:2px solid var(--line);border-radius:12px;padding:14px;font:inherit;margin-bottom:14px}}
textarea {{min-height:132px}}
.success {{display:none;background:#ecfdf5;border:2px solid #86efac;border-radius:16px;padding:20px;color:#065f46}}
iframe {{width:100%;height:280px;border:0;border-radius:18px;margin-top:14px}}
footer {{background:var(--dark);color:#cbd5e1;text-align:center;padding:36px 20px}}
.buy-bar {{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:2px solid var(--brand);padding:14px 20px;z-index:100;display:flex;justify-content:center;align-items:center;gap:18px;box-shadow:0 -4px 24px rgba(0,0,0,.12);flex-wrap:wrap}}
.buy-bar span {{font-weight:900;color:#111}}
.tier-panel {{display:none;position:fixed;left:0;right:0;bottom:0;background:#fff;border-top:3px solid var(--brand);z-index:110;padding:34px 24px 100px;box-shadow:0 -18px 60px rgba(0,0,0,.2);max-height:90vh;overflow:auto}}
.tier-panel.active {{display:block}}
.tiers {{max-width:930px;margin:22px auto 0;display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}
.tier {{border:1px solid var(--line);border-radius:18px;padding:22px;background:#fafafa}}
.tier.featured {{border-color:var(--brand);box-shadow:0 18px 45px rgba(0,0,0,.12)}}
.tier b {{font-size:1.8rem}}
.demo-note {{text-align:center;color:#666;margin:0 auto 26px;max-width:760px;font-size:.96rem}}
.confirm-overlay {{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:120;align-items:center;justify-content:center;padding:20px}}
.confirm-overlay.active {{display:flex}}
.confirm-box {{background:#fff;border-radius:24px;padding:30px;max-width:460px;text-align:center}}
@media(max-width:850px) {{.links a:not(.btn){{display:none}}.grid,.split,.contact-grid,.tiers{{grid-template-columns:1fr}}.hero,.hero-in{{min-height:540px}}}}
</style>
</head>
<body>
<div class="top"><div class="wrap"><span>{esc(location)}</span><span>{esc(phone)}</span></div></div>
<header><div class="wrap"><nav><a class="brand" href="#">{esc(name)}</a><div class="links"><a href="#services">Services</a><a href="#audit">Why rebuild</a><a href="#contact" class="btn">Get a Quote</a></div></nav></div></header>
<section class="hero"><img src="{esc(img)}" alt="{esc(v['label'])} for {esc(name)}"><div class="wrap hero-in"><div><span class="eyebrow">{esc(v['label'])}</span><h1>{esc(name)} rebuilt for calls, quotes and trust.</h1><p class="lead">{esc(v['hero'])}</p><div class="hero-actions">{phone_html}<a class="btn secondary" href="#services">View Services</a></div></div></div></section>
<section class="section" id="services"><div class="wrap"><span class="eyebrow">What customers need fast</span><h2>Services made obvious in seconds.</h2><div class="grid">{service_cards(services)}</div></div></section>
<section class="section" id="audit"><div class="wrap split"><div><span class="eyebrow">Current-site problem</span><h2>The gap is visible before anyone reads the fine print.</h2><p>{esc(reason)}</p><p>This demo fixes the basics: clear headline, click-to-call, quote form, service cards, trust cues, address, map and a persistent purchase CTA.</p></div><div class="audit-card"><h3>Rebuild focuses on</h3><ul>{proof}<li>Mobile-first layout</li><li>One clear conversion path</li></ul><p style="margin-top:18px"><strong>Original checked:</strong><br>{esc(original_url or 'No working website listed')}</p></div></div></section>
<section class="section contact" id="contact"><div class="wrap"><span class="eyebrow">Get in touch</span><h2>Request a quote from {esc(name)}.</h2><div class="contact-grid"><form id="cf" action="https://formsubmit.co/ajax/{esc(form_email)}" method="POST"><input type="hidden" name="_subject" value="New enquiry from {esc(name)} demo site"><input type="hidden" name="_template" value="table"><label>Name</label><input name="name" required><label>Email</label><input name="email" type="email" required><label>What do you need?</label><textarea name="message" required placeholder="Tell us what you need help with..."></textarea><button class="btn" type="submit">Send Message</button><div id="sf" class="success"><strong>Message sent.</strong><br>Thanks - the team will get back to you shortly.</div></form><div class="contact-card"><h3>Contact details</h3><p><strong>Phone:</strong> <a href="tel:{esc(tel)}">{esc(phone)}</a></p>{email_html}<p><strong>Address:</strong> {esc(location)}</p><iframe class="map-frame" loading="lazy" src="https://www.google.com/maps?q={esc(map_q)}&output=embed"></iframe></div></div></div></section>
<footer>{esc(name)} - {esc(v['label'])}</footer>
<div class="buy-bar" id="bb"><span>Want this site for your business?</span><button class="btn" onclick="showTiers()">Get This Site - from £149</button><button class="btn secondary" onclick="showNI()">Not For Me</button></div>
<div class="tier-panel" id="tp"><div style="max-width:930px;margin:auto;position:relative"><button style="position:absolute;right:0;top:0;border:0;background:none;font-size:2rem;cursor:pointer" onclick="hideTiers()">×</button><h2 style="text-align:center">Get Your Site</h2><p class="demo-note">Pick the package that fits. No monthly fees. No lock-in.<br><strong>Images are for demo purposes only.</strong> We swap in your own photos/logo during handover.</p><div class="tiers"><div class="tier"><h3>Buy Outright</h3><b>£149</b><p>Pay once. Own the page. We deploy it and transfer the files.</p><a class="btn" href="{stripe_url(BUY_OUTRIGHT_URL, slug)}">Buy - £149</a></div><div class="tier featured"><h3>Hosted + Edits</h3><b>£399</b><p>12 months hosting, setup and two edit rounds included.</p><a class="btn" href="{stripe_url(HOSTED_URL, slug)}">Buy - £399</a></div><div class="tier"><h3>Not Sure Yet?</h3><b>Free</b><p>Book a 30-minute discovery call and we’ll talk through what you need.</p><a class="btn secondary" href="{SCHEDULE_CALL_URL}">Schedule a Discovery Call</a></div></div></div></div>
<div class="confirm-overlay" id="co"><div class="confirm-box"><h3>Remove this demo?</h3><p>No problem. This demo for {esc(name)} will be taken down within 12 hours.</p><button class="btn secondary" onclick="hideNI()">Keep It</button> <button class="btn" onclick="doDel()">Remove It</button></div></div>
<script>
function showTiers(){{document.getElementById('tp').classList.add('active');document.getElementById('bb').style.display='none'}}
function hideTiers(){{document.getElementById('tp').classList.remove('active');document.getElementById('bb').style.display='flex'}}
function showNI(){{document.getElementById('co').classList.add('active')}}function hideNI(){{document.getElementById('co').classList.remove('active')}}
async function doDel(){{document.querySelector('#co .confirm-box').innerHTML='<h3>Thanks for letting us know</h3><p>This demo will be removed within 12 hours.</p>';try{{await fetch('https://formsubmit.co/ajax/{esc(form_email)}',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{_subject:'DELETE REQUEST: {esc(name)} declined their demo',demo:'{esc(slug)}'}})}})}}catch(e){{}}}}
document.getElementById('cf').addEventListener('submit',async function(e){{e.preventDefault();let f=e.target,b=f.querySelector('button');b.textContent='Sending...';b.disabled=true;let p={{}};new FormData(f).forEach((v,k)=>p[k]=v);try{{await fetch(f.action,{{method:'POST',headers:{{'Content-Type':'application/json','Accept':'application/json'}},body:JSON.stringify(p)}});f.querySelectorAll('label,input,textarea,button').forEach(x=>x.style.display='none');document.getElementById('sf').style.display='block';}}catch(err){{b.textContent='Send Message';b.disabled=false;alert('Sorry, something went wrong. Please call instead.')}}}})
</script>
</body></html>"""


def build(slug: str) -> bool:
    p = EXTRACTED / f"{slug}.json"
    if not p.exists():
        print(f"missing cache: {p}")
        return False
    data = json.loads(p.read_text())
    data.setdefault("slug", slug)
    html_out = generate(data)
    (DEMOS / f"{slug}.html").write_text(html_out, encoding="utf-8")
    (DOCS_DEMOS / f"{slug}.html").write_text(html_out, encoding="utf-8")
    print(f"Built trade demo: {slug}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: generate_trade_demo.py <slug> [slug...]")
        sys.exit(1)
    ok = True
    for slug in sys.argv[1:]:
        ok = build(slug) and ok
    sys.exit(0 if ok else 1)
