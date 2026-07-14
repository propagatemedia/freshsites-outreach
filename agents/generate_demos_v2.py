#!/usr/bin/env python3
"""
Demo Generator v2 - High Value Output
Uses rich scraped data to build non-generic, high-conversion landing pages.
Replaces the old template-driven generator.
"""
import json, re, sys
from pathlib import Path
from datetime import datetime
from string import Template

DEMOS_DIR = Path(__file__).parent.parent / "demos"
DOCS_DIR = Path(__file__).parent.parent / "docs" / "demos"
EXTRACTED_DIR = Path(__file__).parent.parent / "extracted"
DEMOS_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True, parents=True)

# Unsplash images for garage sites (verified working)
IMAGES = {
    "hero_garage": "https://images.unsplash.com/photo-1615906655593-ad0386982a0f?w=1600&q=80",
    "hero_workshop": "https://images.unsplash.com/photo-1621904259206-8c5b2db9435f?w=1600&q=80",
    "about_mechanic": "https://images.unsplash.com/photo-1530549387789-4c1017266685?w=800&q=80",
    "service_mot": "https://images.unsplash.com/photo-1632823469850-2f5d6d66d3e9?w=800&q=80",
    "service_tyres": "https://images.unsplash.com/photo-1626668893632-6f3a446e1c9c?w=800&q=80",
    "service_repairs": "https://images.unsplash.com/photo-1607860108855-64d2074a5d2d?w=800&q=80",
    "service_diagnostic": "https://images.unsplash.com/photo-1597253312687-6f5f5b5b5b5b?w=800&q=80",
    "service_brakes": "https://images.unsplash.com/photo-1601362840469-51d08182b6ce?w=800&q=80",
    "service_engine": "https://images.unsplash.com/photo-1487754180261-fd6d0d1c7b9e?w=800&q=80",
    "service_general": "https://images.unsplash.com/photo-1506140488892-2e95a3d5b8c0?w=800&q=80",
}

SERVICE_ICONS = {
    "mot": "MOT",
    "servicing": "Servicing",
    "service": "Servicing",
    "repair": "Repairs",
    "tyre": "Tyres",
    "exhaust": "Exhaust",
    "clutch": "Clutch",
    "brake": "Brakes",
    "diagnostic": "Diagnostics",
    "air con": "Air Con",
    "timing": "Timing Belt",
    "collection": "Collection",
    "recovery": "Recovery",
    "battery": "Battery",
    "suspension": "Suspension",
}


def get_service_icon(service_name: str) -> str:
    low = service_name.lower()
    for kw, icon in SERVICE_ICONS.items():
        if kw in low:
            return icon
    return service_name[:20]


def generate_demo(data: dict) -> str:
    """Generate a high-quality, non-generic demo from rich scraped data."""
    name = data.get("name", "Garage")
    phone = data.get("phone", "")
    email = data.get("email", "")
    location = data.get("location", "")
    hours = data.get("hours", "")
    services = data.get("services", ["MOT", "Servicing", "Repairs"])
    about = data.get("about", "")
    brand = data.get("brand_color", "#D32F2F")
    trust = data.get("trust_signals", [])
    slug = data.get("slug", "")

    # Build service cards
    service_cards = []
    for i, svc in enumerate(services[:8]):
        icon = get_service_icon(svc)
        service_cards.append(f"""
        <div class="service-card">
            <div class="service-icon">{icon}</div>
            <h3>{svc}</h3>
        </div>""")

    services_html = "\n".join(service_cards)

    # Trust signals
    trust_html = ""
    if trust:
        trust_badges = []
        for t in trust[:5]:
            trust_badges.append(f"<span class='trust-badge'>{t.title()}</span>")
        trust_html = f"""
        <section class="trust-section">
            <div class="container">
                <div class="trust-badges">{''.join(trust_badges)}</div>
            </div>
        </section>"""

    # Hours section
    hours_html = f"<p><strong>Hours:</strong> {hours}</p>" if hours else ""

    # Email section
    email_html = f"<p><strong>Email:</strong> <a href='mailto:{email}' style='color:var(--b)'>{email}</a></p>" if email else ""

    # Map
    map_query = location.replace(",", "+").replace(" ", "+") if location else name.replace(" ", "+")
    map_url = f"https://www.google.com/maps?q={map_query}&output=embed"

    # About section
    about_html = ""
    if about:
        about_html = f"""
        <section class="about-section">
            <div class="container">
                <h2>About {name}</h2>
                <p>{about}</p>
            </div>
        </section>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | {' | '.join(services[:3])} | {location.split(',')[-1].strip() if location else 'Powys'}</title>
    <style>
        :root {{ --b: {brand}; --d: #1a1a1a; --g: #f5f5f5; }}
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:system-ui,-apple-system,sans-serif; color:#222; line-height:1.6; }}
        a {{ text-decoration:none; }}

        .top-bar {{ background:#1a1a1a; color:#fff; padding:10px 24px; font-size:0.9rem; text-align:center; }}
        .top-bar a {{ color:#fff; font-weight:600; }}

        nav {{ background:#fff; border-bottom:1px solid #eee; padding:16px 24px; position:sticky; top:0; z-index:100; box-shadow:0 2px 8px rgba(0,0,0,0.04); }}
        .nav-inner {{ max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; align-items:center; }}
        .logo {{ font-weight:700; font-size:1.4rem; color:var(--b); }}
        .nav-links a {{ margin-left:24px; color:#333; font-weight:500; }}
        .nav-links a:hover {{ color:var(--b); }}

        .btn {{ background:var(--b); color:#fff; padding:12px 28px; border-radius:8px; font-weight:600; display:inline-block; border:none; cursor:pointer; font-size:0.95rem; }}
        .btn:hover {{ opacity:0.9; }}

        .hero {{ position:relative; background:linear-gradient(rgba(0,0,0,0.6),rgba(0,0,0,0.6)),url('{IMAGES['hero_garage']}') center/cover; color:#fff; padding:140px 24px; text-align:center; overflow:hidden; }}
        .hero img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; z-index:-1; }}
        .hero h1 {{ font-size:3rem; margin-bottom:16px; line-height:1.2; }}
        .hero p {{ font-size:1.25rem; max-width:640px; margin:0 auto 32px; opacity:0.95; }}
        .hero .btn {{ font-size:1.1rem; padding:16px 40px; }}

        .container {{ max-width:1200px; margin:0 auto; padding:80px 24px; }}
        .section-title {{ text-align:center; font-size:2.2rem; margin-bottom:48px; }}

        .services-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:24px; }}
        .service-card {{ border:1px solid #eee; padding:32px 24px; border-radius:12px; text-align:center; transition:transform 0.2s,box-shadow 0.2s; }}
        .service-card:hover {{ transform:translateY(-4px); box-shadow:0 8px 24px rgba(0,0,0,0.08); }}
        .service-icon {{ background:{brand}15; color:var(--b); width:60px; height:60px; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 16px; font-size:0.8rem; font-weight:700; }}

        .about-section {{ background:#f8f8f8; }}
        .about-section .container {{ max-width:800px; text-align:center; }}
        .about-section p {{ font-size:1.15rem; margin-top:16px; }}

        .trust-section {{ background:#fff; padding:40px 24px; border-top:1px solid #eee; border-bottom:1px solid #eee; }}
        .trust-badges {{ display:flex; gap:16px; justify-content:center; flex-wrap:wrap; }}
        .trust-badge {{ background:{brand}10; color:var(--b); padding:8px 20px; border-radius:50px; font-size:0.9rem; font-weight:600; }}

        .contact-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:40px; }}
        .form-group {{ margin-bottom:16px; }}
        .form-group label {{ display:block; font-weight:600; font-size:0.9rem; margin-bottom:6px; }}
        .form-group input, .form-group textarea {{ width:100%; padding:14px; border:1px solid #ddd; border-radius:8px; font-size:1rem; }}
        .form-group textarea {{ min-height:120px; resize:vertical; }}
        .success-msg {{ display:none; background:#ecfdf5; padding:24px; border-radius:12px; margin-top:16px; }}
        .map-frame {{ width:100%; height:320px; border:0; border-radius:12px; }}
        .contact-details p {{ margin:8px 0; font-size:1.05rem; }}
        .contact-details a {{ color:var(--b); font-weight:600; }}

        footer {{ background:#1a1a1a; color:#888; padding:32px 24px; text-align:center; font-size:0.9rem; }}

        @media(max-width:768px) {{
            .nav-links a {{ display:none; }}
            .nav-links .btn {{ display:inline-block; }}
            .hero h1 {{ font-size:2rem; }}
            .contact-grid {{ grid-template-columns:1fr; }}
            .hero {{ padding:80px 24px; }}
        }}
    </style>
</head>
<body>

<div class="top-bar">
    {location} &nbsp;|&nbsp; <a href="tel:{phone}">{phone}</a>
</div>

<nav>
    <div class="nav-inner">
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
    <h1>{name}</h1>
    <p>{' | '.join(services[:3])} in {location.split(',')[-1].strip() if location else 'Powys, Wales'}</p>
    <a href="#contact" class="btn">Book Your Vehicle</a>
</header>

<section id="services" class="container">
    <h2 class="section-title">Our Services</h2>
    <div class="services-grid">
        {services_html}
    </div>
</section>

{about_html}

{trust_html}

<section id="contact" class="container">
    <h2 class="section-title">Get In Touch</h2>
    <div class="contact-grid">
        <div>
            <form id="cf">
                <div class="form-group">
                    <label>Name</label>
                    <input type="text" name="name" required placeholder="Your name">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" required placeholder="you@example.com">
                </div>
                <div class="form-group">
                    <label>Message</label>
                    <textarea name="message" rows="5" required placeholder="How can we help?"></textarea>
                </div>
                <button type="submit" class="btn" style="width:100%;font-size:1.05rem;padding:16px;">Send Message</button>
            </form>
            <div id="sf" class="success-msg">
                <strong>Thank you.</strong> We'll get back to you within 24 hours.
            </div>
        </div>
        <div class="contact-details">
            <h3 style="margin-bottom:16px;">Contact Details</h3>
            <p><strong>Phone:</strong> <a href="tel:{phone}">{phone}</a></p>
            {email_html}
            <p><strong>Address:</strong> {location}</p>
            {hours_html}
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
    """Build a demo from an extracted JSON cache."""
    cache_path = EXTRACTED_DIR / f"{slug}.json"
    if not cache_path.exists():
        print(f"  No cache for {slug}")
        return False

    data = json.loads(cache_path.read_text())

    # Generate
    html = generate_demo(data)

    # Write to demos/ and docs/demos/
    (DEMOS_DIR / f"{slug}.html").write_text(html)
    (DOCS_DIR / f"{slug}.html").write_text(html)

    print(f"  Built: {slug}.html")
    return True


def build_all():
    """Build demos for all cached sites."""
    caches = list(EXTRACTED_DIR.glob("*.json"))
    if not caches:
        print("No cached sites found.")
        return

    built = 0
    for cache in caches:
        slug = cache.stem
        if build_from_cache(slug):
            built += 1

    print(f"\nBuilt {built} demos -> demos/ and docs/demos/")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        build_from_cache(sys.argv[1])
    else:
        build_all()
