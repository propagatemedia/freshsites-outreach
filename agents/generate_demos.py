#!/usr/bin/env python3
"""Generate demos from extracted JSON cache in extracted/*.json."""
import json, re
import shutil
from pathlib import Path
from string import Template

EXTRACTED_DIR = Path(__file__).parent.parent / "extracted"
DEMOS_DIR = Path(__file__).parent.parent / "demos"
DOCS_DIR = Path(__file__).parent.parent / "docs" / "demos"

IMAGES = {
    "hero_workshop": "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?w=1600&h=700&fit=crop&q=80",
    "about_mechanic": "https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=600&h=500&fit=crop&q=80",
    "svc_workshop": "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?w=500&h=280&fit=crop&q=80",
    "svc_diagnostics": "https://images.unsplash.com/photo-1578844251758-2f71da64c96f?w=500&h=280&fit=crop&q=80",
    "svc_tyres": "https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?w=500&h=280&fit=crop&q=80",
    "svc_brakes": "https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=500&h=280&fit=crop&q=80",
    "svc_servicing": "https://images.unsplash.com/photo-1625047509168-a7026f36de04?w=500&h=280&fit=crop&q=80",
    "svc_engine": "https://images.unsplash.com/photo-1487754180451-c456f719a1fc?w=500&h=280&fit=crop&q=80",
    "svc_mot": "https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=500&h=280&fit=crop&q=80",
    "svc_exhaust": "https://images.unsplash.com/photo-1606577924006-27d39b132ae2?w=500&h=280&fit=crop&q=80",
    "svc_clutch": "https://images.unsplash.com/photo-1551522435-a13afa10f103?w=500&h=280&fit=crop&q=80",
}

SVC_MAP = {
    "mot": "svc_mot", "service": "svc_servicing", "repair": "svc_workshop",
    "diagnos": "svc_diagnostics", "tyre": "svc_tyres", "brake": "svc_brakes",
    "clutch": "svc_clutch", "exhaust": "svc_exhaust", "batter": "svc_engine",
    "tuning": "svc_engine", "remap": "svc_diagnostics", "air con": "svc_servicing",
    "timing": "svc_engine", "gearbox": "svc_engine", "suspension": "svc_workshop",
    "wheel": "svc_tyres", "collection": "svc_workshop", "default": "svc_workshop",
}

DESC_MAP = {
    "mot": "DVSA approved testing to keep your vehicle road legal.",
    "service": "Full and interim servicing to maintain peak performance.",
    "repair": "Fast, reliable repairs on all makes and models.",
    "brake": "Professional brake disc and pad replacement for safety.",
    "clutch": "Complete clutch and dual mass flywheel replacements.",
    "tyre": "Supply, fitting and puncture repairs at great prices.",
    "exhaust": "Exhaust repairs and replacement using quality parts.",
    "diagnos": "Advanced fault finding using the latest technology.",
    "air con": "Full air conditioning service and re-gas.",
    "timing": "Essential cambelt changes to protect your engine.",
    "batter": "Quality battery testing and same-day fitting.",
    "wheel": "Wheel balancing, tracking and alignment services.",
    "collection": "Local collection and delivery for your convenience.",
    "default": "Professional service you can trust.",
}

T = Template(open(Path(__file__).parent / "demo_template.html").read() if (Path(__file__).parent / "demo_template.html").exists() else """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>:root{--b:${color};--d:#1a1a1a}
*{box-sizing:border-box}body{margin:0;padding:0;font-family:'Inter',sans-serif;color:#1a1a1a;background:#fff;line-height:1.6}
img{max-width:100%;display:block}
a{text-decoration:none;transition:all .2s}
.top-bar{background:var(--d);color:#fff;padding:10px 24px;font-size:.8rem;text-align:center}
.top-bar a{color:#fff;font-weight:600}
nav{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.97);backdrop-filter:blur(8px);border-bottom:1px solid #e5e5e5}
.nav-inner{max-width:1200px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between;height:68px}
.logo{font-weight:800;font-size:1.25rem;color:var(--b)}
.nav-links{display:flex;gap:36px;align-items:center}.nav-links a{font-weight:500;font-size:.9rem;color:#333}.nav-links a:hover{color:var(--b)}
.btn{background:var(--b);color:#fff;padding:10px 22px;border-radius:6px;font-weight:600;font-size:.85rem;display:inline-block;border:none;cursor:pointer}
.btn:hover{opacity:.9}
.btn-o{background:transparent;color:var(--b);padding:10px 18px;border-radius:6px;font-weight:600;font-size:.85rem;border:1.5px solid var(--b);display:inline-block;cursor:pointer}
.btn-o:hover{background:var(--b);color:#fff}
.hero{position:relative;height:600px;overflow:hidden}
.hero img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center}
.hero-overlay{position:absolute;inset:0;background:linear-gradient(90deg,${overlay} 0%,${overlay2} 60%,transparent 100%)}
.hero-content{position:absolute;inset:0;display:flex;align-items:center}
.hero-inner{max-width:1200px;margin:0 auto;padding:0 24px;width:100%}
.hero-text{max-width:560px}
.badge{display:inline-flex;align-items:center;gap:8px;background:${bg};border:1px solid rgba(255,255,255,.4);padding:6px 14px;border-radius:50px;font-size:.75rem;font-weight:600;color:#fff;text-transform:uppercase;letter-spacing:.08em;margin-bottom:20px}
.badge-dot{width:6px;height:6px;background:#fff;border-radius:50%;display:inline-block}
.hero h1{font-size:3.2rem;font-weight:800;color:#fff;line-height:1.05;letter-spacing:-.03em;margin:0 0 16px}
.hero p{font-size:1.15rem;color:rgba(255,255,255,.85);margin:0 0 28px;max-width:440px}
.hero-btns{display:flex;gap:14px;flex-wrap:wrap}
.btn-gh{background:transparent;color:#fff;padding:14px 24px;border-radius:8px;font-weight:600;font-size:1rem;border:1.5px solid rgba(255,255,255,.35);display:inline-block}.btn-gh:hover{border-color:#fff}
.trust{background:#f8f8f8;border-bottom:1px solid #e5e5e5}
.trust-inner{max-width:1200px;margin:0 auto;padding:32px 24px;display:flex;justify-content:space-around;align-items:center;flex-wrap:wrap;gap:24px}.trust-item{text-align:center}.trust-item strong{display:block;font-size:1.8rem;font-weight:800;color:var(--b)}.trust-item span{font-size:.8rem;color:#666;text-transform:uppercase;letter-spacing:.05em}
section{padding:80px 24px}.section-inner{max-width:1200px;margin:0 auto}
.section-header{text-align:center;margin-bottom:56px}.section-header span{display:inline-block;color:var(--b);font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.18em;margin-bottom:12px}.section-header h2{font-size:2.4rem;font-weight:800;color:#1a1a1a;letter-spacing:-.02em;margin:0}.section-header p{color:#666;font-size:1.1rem;margin:12px auto 0;max-width:500px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:32px}
.card{border:1px solid #e5e5e5;border-radius:12px;overflow:hidden;transition:all .3s}.card:hover{box-shadow:0 8px 24px rgba(0,0,0,.08)}.card img{width:100%;height:200px;object-fit:cover;object-position:center}.card-body{padding:28px}.card-body h3{font-size:1.2rem;font-weight:700;color:#1a1a1a;margin:0 0 8px}.card-body p{color:#666;font-size:.95rem;margin:0}
.about{background:#f8f8f8}.about-grid{display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:center}.about-text span{display:inline-block;color:var(--b);font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.18em;margin-bottom:12px}.about-text h2{font-size:2.4rem;font-weight:800;color:#1a1a1a;letter-spacing:-.02em;margin:0 0 20px}.about-text p{color:#444;font-size:1.05rem;margin:0 0 16px}.about-img{width:100%;border-radius:12px;box-shadow:0 20px 40px rgba(0,0,0,.12)}
.cta{background:var(--d);color:#fff;text-align:center}.cta-inner{max-width:800px;margin:0 auto}.cta span{display:inline-block;color:var(--b);font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.18em;margin-bottom:16px}.cta h2{font-size:2.4rem;font-weight:800;margin:0 0 16px}.cta>p{font-size:1.1rem;color:rgba(255,255,255,.75);margin:0 0 28px}
.phone{font-size:2rem;font-weight:800;color:#fff;display:block;margin-bottom:8px;text-decoration:none}
.phone:hover{color:var(--b)}.hours{font-size:.85rem;color:rgba(255,255,255,.5);margin:0 0 20px}
footer{background:#0d0d0d;color:rgba(255,255,255,.4);padding:40px 24px 24px;font-size:.85rem}.footer-inner{max-width:1200px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px}footer strong{color:#fff;font-size:1rem}
.contact-sec{background:#f8f8f8;padding:80px 24px}.contact-grid{display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:start}.contact-form{background:#fff;padding:40px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.06)}.form-group{margin-bottom:20px}.form-group label{display:block;font-weight:600;font-size:.9rem;margin-bottom:8px;color:#1a1a1a}.form-group input,.form-group textarea{width:100%;padding:12px 16px;border:1px solid #e5e5e5;border-radius:8px;font-family:inherit;font-size:1rem}.form-group textarea{resize:vertical;min-height:120px}
.contact-details{background:#fff;padding:40px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.06)}.contact-details h3{margin:0 0 16px;font-size:1.2rem}.contact-details p{margin:0 0 12px;color:#555;font-size:.95rem}.contact-details strong{color:#1a1a1a}
.map-frame{width:100%;height:280px;border-radius:8px;border:none;margin-top:16px}
.buy-bar{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:2px solid var(--b);padding:14px 24px;z-index:100;display:flex;justify-content:center;align-items:center;gap:20px;box-shadow:0 -4px 20px rgba(0,0,0,.1);flex-wrap:wrap}.buy-bar span{font-weight:600;color:#1a1a1a;font-size:.95rem}
.tier-panel{display:none;position:fixed;bottom:0;left:0;right:0;background:#f8f8f8;border-top:3px solid var(--b);padding:40px 24px 100px;z-index:90;max-height:90vh;overflow-y:auto;box-shadow:0 -8px 40px rgba(0,0,0,.15)}.tier-panel.active{display:block}.tiers{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.tier{background:#fff;border:2px solid #e5e5e5;border-radius:12px;padding:28px;text-align:center;position:relative;display:flex;flex-direction:column}.tier.featured{border-color:var(--b);box-shadow:0 8px 24px rgba(0,0,0,.08)}.tier-badge{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--b);color:#fff;padding:4px 16px;border-radius:50px;font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em}.tier h4{font-size:1.05rem;font-weight:700;color:#1a1a1a;margin:0 0 4px}.tier .price{font-size:2.2rem;font-weight:800;color:#1a1a1a;margin:0}.tier .price span{font-size:.85rem;font-weight:500;color:#888}.tier ul{list-style:none;padding:0;margin:0 0 20px;text-align:left;flex-grow:1}.tier ul li{padding:5px 0;border-bottom:1px solid #f0f0f0;color:#444;font-size:.85rem}.tier .btn{display:block;width:100%;padding:10px;border-radius:6px;font-weight:600;text-align:center;margin-bottom:8px}
.confirm-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:200;align-items:center;justify-content:center}.confirm-overlay.active{display:flex}.confirm-box{background:#fff;border-radius:12px;padding:32px;max-width:420px;width:90%;text-align:center}
.removed-bar{display:none;position:fixed;bottom:0;left:0;right:0;background:#1a1a1a;color:#fff;padding:14px 24px;z-index:100;text-align:center}.removed-bar.active{display:block}.removed-bar a{color:var(--b);font-weight:600}
.success-msg{display:none;background:#ecfdf5;border:1px solid #a7f3d0;border-radius:12px;padding:40px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.06)}.success-icon{width:48px;height:48px;background:#059669;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.5rem;margin:0 auto 16px}
@media(max-width:768px){.hero h1{font-size:2rem}.hero{height:400px}.cards,.tiers,.contact-grid{grid-template-columns:1fr}.about-grid{grid-template-columns:1fr}.nav-links{display:none}}
</style></head>
<body>

<div class="top-bar"><span>${loc}</span> | <a href="tel:${phone}" style="color:#fff;font-weight:600">${phone}</a></div>

<nav><div class="nav-inner"><a href="#" class="logo">${name}</a><div class="nav-links"><a href="#services">Services</a><a href="#about">About</a><a href="#contact">Contact</a><a href="tel:${phone}" class="btn">Call Now</a></div></div></nav>

<section class="hero">
<img src="${hero_img}" alt="${name}"><div class="hero-overlay"></div>
<div class="hero-content"><div class="hero-inner"><div class="hero-text">
<div class="badge"><span class="badge-dot"></span>${badge}</div>
<h1>${hero}</h1><p>${desc}</p>
<div class="hero-btns"><a href="tel:${phone}" class="btn" style="padding:14px 28px;font-size:1rem">Call ${phone}</a><a href="#services" class="btn-gh">Our Services</a></div>
</div></div></div>
</section>

<div class="trust"><div class="trust-inner"><div class="trust-item"><strong>${t1}</strong><span>${t1s}</span></div><div class="trust-item"><strong>${t2}</strong><span>${t2s}</span></div><div class="trust-item"><strong>${t3}</strong><span>${t3s}</span></div><div class="trust-item"><strong>${t4}</strong><span>${t4s}</span></div></div></div>

<section id="services"><div class="section-inner"><div class="section-header"><span>What We Offer</span><h2>Our Services</h2><p>Comprehensive garage services for cars and light commercial vehicles.</p></div><div class="cards">${cards}</div></div></section>

<section id="about" class="about"><div class="section-inner"><div class="about-grid"><div class="about-text"><span>About Us</span><h2>${about_h}</h2>${about_p}<a href="tel:${phone}" class="btn" style="margin-top:8px">Call Us Today</a></div><div><img src="${about_img}" alt="${name} workshop" class="about-img"></div></div></div></section>

<section id="contact" class="contact-sec"><div class="section-inner"><div class="section-header"><span>Get In Touch</span><h2>Contact ${name}</h2><p>Book your vehicle in, request a quote, or ask about our services.</p></div><div class="contact-grid"><div class="contact-form"><form id="cf"><div class="form-group"><label>Name</label><input type="text" name="name" required placeholder="Your name"></div><div class="form-group"><label>Email</label><input type="email" name="email" required placeholder="you@example.com"></div><div class="form-group"><label>Message</label><textarea name="message" rows="5" required placeholder="How can we help?"></textarea></div><button type="submit" class="btn" style="width:100%;border:none;cursor:pointer;padding:14px 24px;font-size:1rem">Send Message</button></form><div id="sf" class="success-msg"><div class="success-icon">&#10003;</div><h3 style="color:#065f46;margin:0 0 8px;font-size:1.2rem">Message Sent!</h3><p style="color:#047857;margin:0;font-size:.95rem">Thank you. We will get back to you within 24 hours.</p></div></div><div class="contact-details"><h3>${name}</h3><p><strong>Phone:</strong> <a href="tel:${phone}" style="color:var(--b);font-weight:600">${phone}</a></p><p><strong>Address:</strong> ${loc}</p><p><strong>Hours:</strong> ${hours}</p><iframe class="map-frame" src="${map}" loading="lazy" allowfullscreen></iframe></div></div></div></section>

<footer><div class="footer-inner"><div><strong>${name}</strong><span style="margin-left:16px">${loc}</span></div><div style="display:flex;gap:20px"><span>2024 ${name}</span></div></div></footer>

<div class="buy-bar" id="bb"><span>Want this site for your garage?</span><button class="btn" onclick="showTiers()">Get This Site - from 149</button><button class="btn-o" onclick="showNI()">Not For Me</button></div>

<div class="tier-panel" id="tp"><div class="section-inner" style="position:relative"><button style="position:absolute;top:0;right:0;font-size:1.5rem;color:#999;cursor:pointer;background:none;border:none" onclick="hideTiers()">&times;</button><h3 style="text-align:center;font-size:1.5rem;margin:0 0 8px">Get Your Site</h3><p style="text-align:center;color:#666;margin:0 0 32px">Pick the package that fits. No monthly fees. No lock-in.</p><div class="tiers"><div class="tier"><h4>Buy Outright</h4><p class="price">149 <span>one-time</span></p><ul><li>Complete page deployed live</li><li>Free Vercel account setup</li><li>Ownership transferred to you</li><li>Add your own custom domain</li></ul><a href="https://buy.stripe.com/14AaENc4oeYBgfk26R5EY0f" class="btn btn-primary">Buy - 149</a></div><div class="tier featured"><div class="tier-badge">Popular</div><h4>Hosted + Edits</h4><p class="price">399 <span>one-time</span></p><ul><li>Live deployment to Vercel</li><li>12 months hosting included</li><li>2 rounds of edits included</li><li>Email support</li></ul><a href="https://buy.stripe.com/fZu4gpecw2bPbZ4dPz5EY0g" class="btn btn-primary">Buy - 399</a></div><div class="tier"><h4>Premium</h4><p class="price">997 <span>first 12 months</span></p><ul><li>Everything in Hosted + Edits</li><li>Voice AI chatbot bolt-on</li><li>Unlimited edits for 12 months</li><li>Priority support</li></ul><button class="btn" onclick="alert('Contact tyrone@propagate.media for Premium setup')">Get This</button></div></div></div></div>

<div class="confirm-overlay" id="co"><div class="confirm-box"><h3>Remove This Demo?</h3><p>This will permanently delete the demo page for ${name}.</p><div style="display:flex;gap:12px;justify-content:center"><button class="btn-o" onclick="hideNI()">Keep It</button><button class="btn" onclick="doDel()" style="background:#666;border-color:#666">Delete Demo</button></div></div></div>
<div class="removed-bar" id="rb"><p>This demo has been permanently removed. <a href="mailto:freshsites@sites.propagate.media">Email us</a> if you change your mind.</p></div>

<script>function showTiers(){document.getElementById('tp').classList.add('active');document.getElementById('bb').style.display='none'}function hideTiers(){document.getElementById('tp').classList.remove('active');document.getElementById('bb').style.display='flex'}function showNI(){document.getElementById('co').classList.add('active')}function hideNI(){document.getElementById('co').classList.remove('active')}function doDel(){document.getElementById('co').classList.remove('active');document.getElementById('bb').style.display='none';document.getElementById('tp').classList.remove('active');document.getElementById('rb').classList.add('active')}document.getElementById('cf').addEventListener('submit',function(e){e.preventDefault();document.getElementById('cf').style.display='none';document.getElementById('sf').style.display='block'});document.getElementById('co').addEventListener('click',function(e){if(e.target===this)hideNI()});document.getElementById('tp').addEventListener('click',function(e){if(e.target===this)hideTiers()})</script>

</body></html>""")


def get_svc_img(svc_name):
    low = svc_name.lower()
    for keyword, img_key in SVC_MAP.items():
        if keyword in low:
            return IMAGES[img_key]
    return IMAGES[SVC_MAP["default"]]


def get_svc_desc(svc_name):
    low = svc_name.lower()
    for keyword, desc in DESC_MAP.items():
        if keyword in low:
            return desc
    return DESC_MAP["default"]


def build_cards(services):
    cards = []
    for svc in services:
        if not svc:
            continue
        url = get_svc_img(svc)
        desc = get_svc_desc(svc)
        cards.append(
            f'<div class="card"><img src="{url}" alt="{svc}" loading="lazy">'
            f'<div class="card-body"><h3>{svc}</h3><p>{desc}</p></div></div>'
        )
    return "".join(cards)


def make_map_url(location):
    q = location.replace(" ", "+")
    return f"https://www.google.com/maps?q={q}&output=embed"


def darkened(hex_color, factor=0.6):
    h = hex_color.lstrip("#")
    r = max(0, int(int(h[0:2], 16) * factor))
    g = max(0, int(int(h[2:4], 16) * factor))
    b = max(0, int(int(h[4:6], 16) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_demo(data):
    name = data["name"]
    slug = data["slug"]
    color = data.get("brand_color", "#c41e3a")
    services = data.get("services", [])
    phone = data.get("phone", "")
    hours = data.get("hours", "")
    location = data.get("location", "")
    about = data.get("about", "Local garage providing professional vehicle services.")
    images = data.get("images", [])

    # Images — use verified Unsplash images only (their own site images may be blocked by hotlink protection)
    hero_img = IMAGES["hero_workshop"]
    about_img = IMAGES["about_mechanic"]
    # Only use their extracted images if they exist and we verify them (disabled for now)
    images = []  # data.get("images", [])

    # Fallback services
    if not services:
        services = ["Servicing & Repairs", "MOT Testing", "Diagnostics", "Tyres", "Brakes", "Clutch"]

    # Phone
    phone = phone or "Call for quote"

    # Years for trust bar
    years = "20+"
    match = re.search(r'(\d{4})', about)
    if match:
        years = str(2024 - int(match.group(1)))

    town = location.split(",")[0].strip() if "," in location else location

    values = {
        "name": name,
        "slug": slug,
        "color": color,
        "dark": "#1a1a1a",
        "overlay": f"{color}d9",
        "overlay2": f"{darkened(color)}cc",
        "bg": f"{color}4d",
        "phone": phone,
        "loc": location,
        "hours": hours,
        "badge": "Local Garage",
        "hero": services[0] if services else "Vehicle Servicing & Repairs",
        "desc": f"Professional garage services in {town}.",
        "hero_img": hero_img,
        "about_img": about_img,
        "t1": years + "+",
        "t1s": "Years Experience",
        "t2": "All Makes",
        "t2s": "& Models",
        "t3": "MOT",
        "t3s": "Testing",
        "t4": "Parts",
        "t4s": "& Labour",
        "cards": build_cards(services),
        "about_h": f"Your Trusted {town} Garage",
        "about_p": "<p>" + about.replace("\n", "</p><p>") + "</p>",
        "map": make_map_url(location),
    }

    # Build safe path
    slug = re.sub(r"\W+", "-", slug)
    return T.substitute(values), slug


def main():
    DEMOS_DIR.mkdir(exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Read leads from DB to ensure 1:1 mapping
    import sqlite3
    conn = sqlite3.connect(str(Path(__file__).parent.parent / "leads" / "freshsites.db"))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT name, website FROM leads WHERE status='demo_built'")
    leads = c.fetchall()
    conn.close()

    built = 0
    for row in leads:
        slug = re.sub(r"\W+", "-", row["website"].replace("https://", "").replace("http://", "").rstrip("/"))
        slug = re.sub(r"^-+|-+$", "", slug)
        cache = EXTRACTED_DIR / f"{slug}.json"
        if not cache.exists():
            print(f"SKIP: {slug} — no extracted cache")
            continue
        data = json.loads(cache.read_text())
        try:
            html, gen_slug = generate_demo(data)
        except Exception as e:
            print(f"SKIP {cache}: {e}")
            continue
        path = DEMOS_DIR / f"{slug}.html"
        path.write_text(html, encoding="utf-8")
        print(f"Built: {path}")
        shutil.copy(path, DOCS_DIR / f"{slug}.html")
        built += 1

    print(f"\nBuilt {built} demos -> demos/ and docs/demos/")


if __name__ == "__main__":
    main()
