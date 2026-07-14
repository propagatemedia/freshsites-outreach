#!/usr/bin/env python3
"""
Demo Generator v3.1 — Award-Winning Design
Fixes: working Pexels images, service descriptions, about image,
removed ridiculous full-width Facebook strip, padding fixes.

Design principles from CRO + copywriting + site-architecture skills.
"""
import json, re, sys
from pathlib import Path

DEMOS_DIR = Path(__file__).parent.parent / "demos"
DOCS_DIR = Path(__file__).parent.parent / "docs" / "demos"
EXTRACTED_DIR = Path(__file__).parent.parent / "extracted"
DEMOS_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True, parents=True)

# All verified working Pexels images - actual garage/mechanic photos
IMAGES = {
    "hero": "https://images.pexels.com/photos/4116231/pexels-photo-4116231.jpeg?auto=compress&w=1600",
    "about": "https://images.pexels.com/photos/8985462/pexels-photo-8985462.jpeg?auto=compress&w=800",
    "mot": "https://images.pexels.com/photos/8986130/pexels-photo-8986130.jpeg?auto=compress&w=600",
    "tyres": "https://images.pexels.com/photos/32208774/pexels-photo-32208774.jpeg?auto=compress&w=600",
    "repairs": "https://images.pexels.com/photos/6870307/pexels-photo-6870307.jpeg?auto=compress&w=600",
    "diagnostic": "https://images.pexels.com/photos/9626877/pexels-photo-9626877.jpeg?auto=compress&w=600",
    "general": "https://images.pexels.com/photos/4116168/pexels-photo-4116168.jpeg?auto=compress&w=600",
    "collection": "https://images.pexels.com/photos/37809545/pexels-photo-37809545.jpeg?auto=compress&w=600",
}

SERVICE_MAP = {
    "mot": ("MOT", "mot", "Class 4 & 7 testing for cars, vans and goods vehicles."),
    "pre-mot": ("PRE-MOT", "mot", "Full pre-MOT inspection to catch issues before your test."),
    "servicing": ("SERVICING", "general", "Full manufacturer-equivalent servicing for all makes and models."),
    "service": ("SERVICING", "general", "Full manufacturer-equivalent servicing for all makes and models."),
    "repair": ("REPAIRS", "repairs", "Expert repairs for engines, brakes, clutches and more."),
    "tyre": ("TYRES", "tyres", "Supply, fitting and puncture repairs for all vehicle types."),
    "puncture": ("TYRES", "tyres", "Quick puncture repairs to get you back on the road."),
    "diagnostic": ("DIAGNOSTICS", "diagnostic", "Advanced diagnostic equipment to find faults fast."),
    "brake": ("BRAKES", "repairs", "Brake pad and disc replacement with quality parts."),
    "clutch": ("CLUTCH", "repairs", "Clutch fitting and flywheel replacement."),
    "exhaust": ("EXHAUST", "general", "Exhaust repair and replacement fitted while you wait."),
    "collection": ("COLLECTION", "collection", "Local collection and delivery service available."),
    "delivery": ("COLLECTION", "collection", "Local collection and delivery service available."),
    "air con": ("AIR CON", "general", "Air conditioning recharge and system repairs."),
    "timing": ("TIMING BELT", "general", "Timing belt and cam belt replacement by specialists."),
    "recovery": ("RECOVERY", "collection", "Vehicle recovery service for breakdowns and accidents."),
    "battery": ("BATTERIES", "general", "Battery testing and replacement with warranty."),
    "suspension": ("SUSPENSION", "repairs", "Shock absorber and suspension repair."),
    "general": ("REPAIRS", "general", "General mechanical repairs and maintenance."),
}

def get_service_meta(name):
    low = name.lower()
    for kw, (tag, img_key, desc) in SERVICE_MAP.items():
        if kw in low:
            return tag, IMAGES[img_key], desc
    return name[:12].upper(), IMAGES["general"], "Professional service by qualified technicians."


def generate_demo(data: dict) -> str:
    name = data.get("name", "Garage")
    phone = data.get("phone", "")
    email = data.get("email", "")
    location = data.get("location", "")
    hours = data.get("hours", "")
    services = data.get("services", ["MOT", "Servicing", "Repairs"])
    about = data.get("about", "")
    brand = data.get("brand_color", "#D32F2F")
    slug = data.get("slug", "")

    town = "Powys, Wales"
    if location:
        parts = [p.strip() for p in location.split(",")]
        if len(parts) >= 2:
            town = parts[-2] if len(parts) >= 3 else parts[-1]

    # Build service cards with images + descriptions
    cards = []
    for svc in services[:6]:
        tag, img, desc = get_service_meta(svc)
        cards.append(f"""        <div class="svc-card">
          <div class="svc-img" style="background-image:url('{img}')"></div>
          <div class="svc-body">
            <span class="svc-tag">{tag}</span>
            <h3>{svc}</h3>
            <p>{desc}</p>
          </div>
        </div>""")

    services_html = "\n".join(cards)

    # About section
    about_html = ""
    if about:
        about_html = f"""      <section id="about" class="about-sec">
        <div class="wrap two-col">
          <div class="about-img" style="background-image:url('{IMAGES['about']}')"></div>
          <div class="about-text">
            <span class="eyebrow">About Us</span>
            <h2>Your local, independent garage</h2>
            <p>{about}</p>
            <a href="#contact" class="btn" style="margin-top:16px;">Get In Touch</a>
          </div>
        </div>
      </section>"""

    email_html = f"<p><strong>Email:</strong> <a href='mailto:{email}' class='brand-link'>{email}</a></p>" if email else ""
    hours_html = f"<p><strong>Hours:</strong> {hours}</p>" if hours else ""
    map_q = location.replace(",", "+").replace(" ", "+") if location else name.replace(" ", "+")
    map_url = f"https://www.google.com/maps?q={map_q}&output=embed"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} | MOT, Servicing & Repairs | {town}</title>
  <style>
    :root {{--b: {brand}; --d: #1a1a1a; --bg: #f7f7f8; --card: #fff; --text: #222; --muted: #666;}}
    * {{margin:0; padding:0; box-sizing:border-box;}}
    body {{font-family:system-ui,-apple-system,'Segoe UI',sans-serif; color:var(--text); line-height:1.7; background:var(--bg);}}
    a {{text-decoration:none;}}
    img {{max-width:100%;}}

    .topbar {{background:var(--d); color:#fff; padding:10px 24px; font-size:0.88rem; text-align:center;}}
    .topbar a {{color:#fff; font-weight:600;}}

    nav {{background:var(--card); border-bottom:1px solid #eee; padding:14px 24px; position:sticky; top:0; z-index:100; box-shadow:0 1px 4px rgba(0,0,0,.03);}}
    .nav-in {{max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; align-items:center;}}
    .logo {{font-weight:800; font-size:1.35rem; color:var(--b);}}
    .nav-links a {{margin-left:24px; color:var(--text); font-weight:500; font-size:0.95rem;}}
    .nav-links a:hover {{color:var(--b);}}

    .btn {{background:var(--b); color:#fff !important; padding:12px 28px; border-radius:8px; font-weight:600; display:inline-block; border:none; cursor:pointer; font-size:0.95rem; transition:opacity .15s;}}
    .btn:hover {{opacity:.88;}}

    .hero {{position:relative; min-height:560px; display:flex; align-items:center; justify-content:center; text-align:center; color:#fff; overflow:hidden;}}
    .hero-bg {{position:absolute; inset:0; width:100%; height:100%; object-fit:cover;}}
    .hero-overlay {{position:absolute; inset:0; background:linear-gradient(rgba(0,0,0,.3),rgba(0,0,0,.4));}}
    .hero-content {{position:relative; z-index:2; max-width:720px; padding:80px 24px;}}
    .hero h1 {{font-size:3rem; line-height:1.15; margin-bottom:12px;}}
    .hero p {{font-size:1.2rem; opacity:.95; margin-bottom:28px;}}
    .hero .btn {{font-size:1.1rem; padding:16px 40px;}}

    .wrap {{max-width:1200px; margin:0 auto; padding:72px 24px;}}
    .eyebrow {{color:var(--b); font-weight:700; font-size:0.78rem; text-transform:uppercase; letter-spacing:.12em;}}
    .sec-title {{font-size:2rem; margin:8px 0 40px; text-align:center;}}

    .svc-grid {{display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:24px;}}
    .svc-card {{background:var(--card); border-radius:14px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,.05); transition:transform .2s,box-shadow .2s;}}
    .svc-card:hover {{transform:translateY(-4px); box-shadow:0 12px 32px rgba(0,0,0,.1);}}
    .svc-img {{height:180px; background-size:cover; background-position:center;}}
    .svc-body {{padding:20px 24px;}}
    .svc-tag {{display:inline-block; background:var(--b)12; color:var(--b); padding:4px 14px; border-radius:50px; font-size:0.72rem; font-weight:700; margin-bottom:8px;}}
    .svc-body h3 {{font-size:1.05rem; margin:0 0 6px; color:var(--text);}}
    .svc-body p {{font-size:0.88rem; color:var(--muted); margin:0; line-height:1.5;}}

    .about-sec {{background:var(--card);}}
    .two-col {{display:grid; grid-template-columns:1fr 1fr; gap:48px; align-items:center;}}
    .about-img {{height:400px; background-size:cover; background-position:center; border-radius:14px;}}
    .about-text p {{font-size:1.1rem; color:var(--muted); margin-top:12px;}}

    .contact-grid {{display:grid; grid-template-columns:1fr 1fr; gap:40px;}}
    .form-grp {{margin-bottom:16px;}}
    .form-grp label {{display:block; font-weight:600; font-size:0.88rem; margin-bottom:6px;}}
    .form-grp input, .form-grp textarea {{width:100%; padding:14px; border:2px solid #e5e5e5; border-radius:10px; font-size:1rem; font-family:inherit; transition:border-color .15s;}}
    .form-grp input:focus, .form-grp textarea:focus {{border-color:var(--b); outline:none;}}
    .form-grp textarea {{min-height:120px; resize:vertical;}}
    .success {{display:none; background:#ecfdf5; padding:20px; border-radius:12px; margin-top:16px; border:2px solid #6ee7b7;}}
    .map-frame {{width:100%; height:320px; border:0; border-radius:14px;}}
    .contact-info p {{margin:6px 0; font-size:1.05rem;}}
    .contact-info .hours-row {{margin-bottom:24px;}}
    .brand-link {{color:var(--b); font-weight:600;}}

    footer {{background:var(--d); color:#888; padding:32px 24px; text-align:center; font-size:0.88rem;}}

    @media(max-width:768px) {{
      .nav-links a {{display:none;}}
      .nav-links .btn {{display:inline-block;}}
      .hero h1 {{font-size:2.1rem;}}
      .two-col, .contact-grid {{grid-template-columns:1fr;}}
      .about-img {{height:240px;}}
      .hero {{min-height:420px;}}
      .hero-content {{padding:60px 24px;}}
    }}
  </style>
</head>
<body>

  <div class="topbar">
    {location} &nbsp;|&nbsp; <a href="tel:{phone}">{phone}</a>
  </div>

  <nav>
    <div class="nav-in">
      <span class="logo">{name}</span>
      <div class="nav-links">
        <a href="#services">Services</a>
        <a href="#about">About</a>
        <a href="#contact">Contact</a>
        <a href="tel:{phone}" class="btn">Call Now</a>
      </div>
    </div>
  </nav>

  <header class="hero">
    <img class="hero-bg" src="{IMAGES['hero']}" alt="Garage workshop">
    <div class="hero-overlay"></div>
    <div class="hero-content">
      <h1>{name}</h1>
      <p>{' | '.join(services[:3])} in {town}</p>
      <a href="#contact" class="btn">Book Your Vehicle</a>
    </div>
  </header>

  <section id="services" class="wrap">
    <span class="eyebrow" style="display:block;text-align:center;">What We Do</span>
    <h2 class="sec-title">Our Services</h2>
    <div class="svc-grid">
{services_html}
    </div>
  </section>

{about_html}

  <section id="contact" class="wrap">
    <span class="eyebrow" style="display:block;text-align:center;">Get In Touch</span>
    <h2 class="sec-title">Book Your Vehicle In</h2>
    <div class="contact-grid">
      <div>
        <form id="cf">
          <div class="form-grp">
            <label>Your Name</label>
            <input type="text" name="name" required placeholder="John Smith">
          </div>
          <div class="form-grp">
            <label>Email</label>
            <input type="email" name="email" required placeholder="you@example.com">
          </div>
          <div class="form-grp">
            <label>Message</label>
            <textarea name="message" rows="5" required placeholder="What do you need? MOT, service, repair?"></textarea>
          </div>
          <button type="submit" class="btn" style="width:100%;font-size:1.05rem;padding:16px;">Send Message</button>
        </form>
        <div id="sf" class="success">
          <strong>Message sent!</strong> We'll get back to you within 24 hours.
        </div>
      </div>
      <div class="contact-info">
        <h3 style="margin-bottom:12px;">Contact Details</h3>
        <p><strong>Phone:</strong> <a href="tel:{phone}" class="brand-link" style="font-size:1.3rem;">{phone}</a></p>
        {email_html}
        <p><strong>Address:</strong> {location}</p>
        <div class="hours-row">{hours_html}</div>
        <iframe class="map-frame" src="{map_url}" loading="lazy" allowfullscreen></iframe>
      </div>
    </div>
  </section>

  <footer>
    {name} &middot; {location}
  </footer>

  <script>
    document.getElementById('cf').addEventListener('submit', function(e) {{
      e.preventDefault();
      document.getElementById('cf').style.display = 'none';
      document.getElementById('sf').style.display = 'block';
    }});
  </script>
</body>
</html>"""

    return html


def build_from_cache(slug: str) -> bool:
    cache_path = EXTRACTED_DIR / f"{slug}.json"
    if not cache_path.exists():
        print(f"  No cache for {slug}")
        return False
    data = json.loads(cache_path.read_text())
    html = generate_demo(data)
    (DEMOS_DIR / f"{slug}.html").write_text(html)
    (DOCS_DIR / f"{slug}.html").write_text(html)
    print(f"  Built: {slug}.html")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        build_from_cache(sys.argv[1])
    else:
        for cache in EXTRACTED_DIR.glob("*.json"):
            build_from_cache(cache.stem)
