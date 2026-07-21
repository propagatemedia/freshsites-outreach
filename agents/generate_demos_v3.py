#!/usr/bin/env python3
"""
Demo Generator v3.1 - Award-Winning Design
Fixes: working Pexels images, service descriptions, about image,
removed ridiculous full-width Facebook strip, padding fixes.

Design principles from CRO + copywriting + site-architecture skills.
"""
import json, re, sys, os, hashlib
from pathlib import Path

DEMOS_DIR = Path(__file__).parent.parent / "demos"
DOCS_DIR = Path(__file__).parent.parent / "docs" / "demos"
EXTRACTED_DIR = Path(__file__).parent.parent / "extracted"
DEMOS_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True, parents=True)

# Approved local images (user-reviewed, optimized)
# Path is relative to the repo root, will be served from GitHub Pages
IMG_BASE = "../assets/img/"
POSTHOG_PROJECT_TOKEN = "phc_xkcXiM3PPU5kMWec3s94BZJGZwyykcEtHLzC6Dg7ooNa"
POSTHOG_API_HOST = "https://eu.i.posthog.com"

def posthog_head(slug: str, business_name: str) -> str:
    """PostHog browser tracking for demo-page visits and key funnel events."""
    safe_slug = json.dumps(slug)
    safe_name = json.dumps(business_name)
    return f"""
  <script>
    !function(t,e){{var o,n,p,r;e.__SV||(window.posthog&&window.posthog.__loaded)||(window.posthog=e,e._i=[],e.init=function(i,s,a){{function g(t,e){{var o=e.split('.');2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){{t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}}}(p=t.createElement('script')).type='text/javascript',p.crossOrigin='anonymous',p.async=!0,p.src=s.api_host.replace('.i.posthog.com','-assets.i.posthog.com')+'/static/array.js',(r=t.getElementsByTagName('script')[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a='posthog',u.people=u.people||[],u.toString=function(t){{var e='posthog';return'posthog'!==a&&(e+='.'+a),t||(e+=' (stub)'),e}},u.people.toString=function(){{return u.toString(1)+'.people (stub)'}},o='init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload getFeatureFlagResult getAllFeatureFlags isFeatureEnabled reloadFeatureFlags updateFlags on onFeatureFlags identify setPersonProperties unsetPersonProperties group resetGroups reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing debug'.split(' '),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])}},e.__SV=1)}}(document,window.posthog||[]);
    posthog.init('{POSTHOG_PROJECT_TOKEN}', {{
      api_host: '{POSTHOG_API_HOST}',
      defaults: '2026-05-30',
      person_profiles: 'identified_only'
    }});
    posthog.register({{lead_slug: {safe_slug}, business_name: {safe_name}, source: 'freshsites_demo'}});
    posthog.capture('demo_viewed', {{lead_slug: {safe_slug}, business_name: {safe_name}}});
  </script>"""

IMAGES = {
    "hero": IMG_BASE + "hero-garage.jpg",
    "about": IMG_BASE + "mechanic-shop.jpg",
    "servicing": IMG_BASE + "servicing.jpg",
    "mot": IMG_BASE + "checklist.jpg",
    "engine": IMG_BASE + "engine-repair.jpg",
    "suspension": IMG_BASE + "suspension.jpg",
    "repairs": IMG_BASE + "repair-1.jpg",
    "repairs_alt": IMG_BASE + "repair-2.jpg",
    "repairs_alt_2": IMG_BASE + "repair-3.jpg",
    "repairs_alt_3": IMG_BASE + "repair-4.jpg",
    "tyres": IMG_BASE + "tyre-change.jpg",
    "tyres_alt_1": IMG_BASE + "tyre-change-2.jpg",
    "tyres_alt_2": IMG_BASE + "tyre-change-3.jpg",
    "general": IMG_BASE + "servicing.jpg",
    "collection": IMG_BASE + "repair-3.jpg",
}

IMAGE_VARIANTS = {
    "hero": [IMAGES["hero"], IMAGES["about"], IMAGES["servicing"], IMAGES["engine"], IMAGES["repairs_alt_3"]],
    "about": [IMAGES["about"], IMAGES["repairs_alt_2"], IMAGES["servicing"], IMAGES["engine"], IMAGES["suspension"]],
    "repairs": [IMAGES["repairs"], IMAGES["repairs_alt"], IMAGES["repairs_alt_2"], IMAGES["repairs_alt_3"], IMAGES["engine"]],
    "servicing": [IMAGES["servicing"], IMAGES["mot"], IMAGES["repairs_alt_2"], IMAGES["about"]],
    "mot": [IMAGES["mot"], IMAGES["servicing"], IMAGES["repairs_alt_2"], IMAGES["tyres_alt_1"]],
    "tyres": [IMAGES["tyres"], IMAGES["tyres_alt_1"], IMAGES["tyres_alt_2"], IMAGES["repairs_alt_2"]],
    "engine": [IMAGES["engine"], IMAGES["repairs_alt_3"], IMAGES["servicing"], IMAGES["repairs"]],
    "suspension": [IMAGES["suspension"], IMAGES["engine"], IMAGES["repairs_alt_2"]],
    "collection": [IMAGES["repairs_alt_2"], IMAGES["tyres_alt_1"], IMAGES["about"]],
}

BLOG_POSTS = [
    {"title":"How to Prepare Your Car for Its MOT","subtitle":"Simple checks that could prevent an avoidable MOT failure.","excerpt":"A few minutes checking bulbs, tyres, wipers, number plates and fluid levels can save time and inconvenience before test day.","image_key":"mot"},
    {"title":"Why Skipping a Car Service Can Cost More Later","subtitle":"Small maintenance delays can turn into expensive mechanical problems.","excerpt":"Old oil, worn filters and unchecked components can accelerate wear. Regular servicing helps protect reliability, fuel economy and resale value.","image_key":"servicing"},
    {"title":"How to Check Your Tyre Tread Depth","subtitle":"A simple safety check every driver should know how to perform.","excerpt":"Tyre tread affects grip, braking and water clearance. This guide explains what to check and why uneven wear deserves professional attention.","image_key":"tyres"},
    {"title":"Warning Signs Your Brakes Need Attention","subtitle":"Small brake changes are easy to ignore - until they become dangerous.","excerpt":"Squealing, grinding, vibration, longer stopping distances and dashboard warnings are signs that a professional brake check should not wait.","image_key":"repairs"},
    {"title":"What Dashboard Warning Lights Usually Mean","subtitle":"A warning light is your car asking for a proper diagnosis.","excerpt":"Some lights are urgent, others are early warnings. A diagnostic check helps avoid guesswork, wasted parts and avoidable breakdowns.","image_key":"engine"},
    {"title":"When Should You Replace Your Timing Belt?","subtitle":"Timing belt failure can destroy an engine without warning.","excerpt":"Mileage, age and manufacturer intervals matter. If the belt history is unclear, a garage check can prevent one of the most expensive failures.","image_key":"engine"},
    {"title":"Why Wheel Alignment Saves Tyres and Fuel","subtitle":"Poor alignment quietly costs money every mile.","excerpt":"Uneven tyre wear, pulling to one side and steering vibration can all point to alignment issues that reduce tyre life and handling.","image_key":"tyres"},
    {"title":"How Often Should You Check Oil and Coolant?","subtitle":"Basic fluid checks prevent avoidable engine damage.","excerpt":"Low oil, coolant leaks and neglected top-ups can turn minor maintenance into major repair bills. Regular checks catch problems early.","image_key":"servicing"},
    {"title":"Before a Long Journey: What to Check","subtitle":"A ten-minute check can prevent roadside stress.","excerpt":"Tyres, fluids, lights, brakes and wipers are the basics worth checking before motorway trips, holidays or heavy daily mileage.","image_key":"mot"},
]

def stable_index(seed: str, length: int, salt: str = "") -> int:
    return int(hashlib.sha256((seed + salt).encode("utf-8")).hexdigest(), 16) % max(length, 1)

def rotate_list(items, seed: str, salt: str = ""):
    if not items:
        return []
    i = stable_index(seed, len(items), salt)
    return items[i:] + items[:i]

def pick_variant(key: str, seed: str, used=None, salt: str = ""):
    used = used or set()
    variants = rotate_list(IMAGE_VARIANTS.get(key, [IMAGES.get(key, IMAGES["repairs"])]), seed, salt)
    for img in variants:
        if img not in used:
            return img
    return variants[0]

def select_blog_posts(seed: str, count: int = 3):
    """Pick a deterministic but varied blog mix per demo slug.

    Avoid the old failure mode where every page showed the same three cards.
    Selection uses independent salted hashes rather than a simple contiguous slice.
    """
    selected = []
    used_titles = set()
    used_images = set()
    for idx in range(count):
        post = BLOG_POSTS[0]
        for attempt in range(len(BLOG_POSTS)):
            post = BLOG_POSTS[stable_index(seed, len(BLOG_POSTS), f"blog-{idx}-{attempt}")]
            if post["title"] not in used_titles:
                break
        p = dict(post)
        p["image"] = pick_variant(p.get("image_key", "repairs"), seed, used_images, f"blog-img-{idx}")
        used_titles.add(p["title"])
        used_images.add(p["image"])
        selected.append(p)
    return selected

SERVICE_MAP = {
    "mot": ("MOT", "mot", "Class 4 & 7 testing for cars, vans and goods vehicles."),
    "pre-mot": ("PRE-MOT", "mot", "Full pre-MOT inspection to catch issues before your test."),
    "servicing": ("SERVICING", "servicing", "Full manufacturer-equivalent servicing for all makes and models."),
    "service": ("SERVICING", "servicing", "Full manufacturer-equivalent servicing for all makes and models."),
    "repair": ("REPAIRS", "repairs", "Expert repairs for engines, brakes, clutches and more."),
    "free tyre safety check": ("TYRE SAFETY", "tyres", "Free tyre safety checks for tread, pressure and visible damage."),
    "tyre services": ("TYRES", "tyres", "Tyre fitting, balancing, alignment checks and puncture support."),
    "laser wheel alignment": ("ALIGNMENT", "tyres", "Laser wheel alignment to reduce tyre wear and improve handling."),
    "wheel alignment": ("ALIGNMENT", "tyres", "Four-wheel alignment to reduce tyre wear and improve handling."),
    "wheel balancing": ("BALANCING", "tyres", "Dynamic wheel balancing for a smoother drive and even tyre wear."),
    "4 wheel": ("ALIGNMENT", "tyres", "Four-wheel alignment to reduce tyre wear and improve handling."),
    "run-flat": ("RUN-FLAT", "tyres", "Run-flat tyre fitting and replacement for modern vehicles."),
    "agricultural": ("AGRI TYRES", "collection", "Tyre support for agricultural vehicles, trailers and working equipment."),
    "trailer": ("TRAILERS", "collection", "Trailer tyre fitting, checks and replacement."),
    "call out": ("CALL OUT", "collection", "Mobile tyre call-out across Adfa, Newtown, Welshpool and surrounding Powys."),
    "tyre": ("TYRES", "tyres", "Supply, fitting and puncture repairs for cars, vans and working vehicles."),
    "puncture": ("PUNCTURES", "tyres", "Quick puncture repairs to get you back on the road."),
    "diagnostic": ("DIAGNOSTICS", "engine", "Advanced diagnostic equipment to find faults fast."),
    "brake": ("BRAKES", "repairs", "Brake pad and disc replacement with quality parts."),
    "clutch": ("CLUTCH", "repairs", "Clutch fitting and flywheel replacement."),
    "exhaust": ("EXHAUST", "engine", "Exhaust repair and replacement fitted while you wait."),
    "collection": ("COLLECTION", "collection", "Local collection and delivery service available."),
    "delivery": ("COLLECTION", "collection", "Local collection and delivery service available."),
    "air con": ("AIR CON", "servicing", "Air conditioning recharge and system repairs."),
    "timing": ("TIMING BELT", "engine", "Timing belt and cam belt replacement by specialists."),
    "recovery": ("RECOVERY", "collection", "Vehicle recovery service for breakdowns and accidents."),
    "battery": ("BATTERIES", "engine", "Battery testing and replacement with warranty."),
    "suspension": ("SUSPENSION", "suspension", "Shock absorber and suspension repair."),
    "general": ("REPAIRS", "repairs", "General mechanical repairs and maintenance."),
}

def get_service_meta(name):
    low = name.lower()
    # Check more specific keywords first (longer matches take priority)
    for kw in sorted(SERVICE_MAP.keys(), key=len, reverse=True):
        if kw in low:
            tag, img_key, desc = SERVICE_MAP[kw]
            return tag, IMAGES.get(img_key, IMAGES["repairs"]), desc
    return name[:12].upper(), IMAGES["repairs"], "Professional service by qualified technicians."


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
    form_email = os.environ.get("FORM_EMAIL", "freshsites@sites.propagate.media")

    town = "Powys, Wales"
    if location:
        parts = [p.strip() for p in location.split(",")]
        if len(parts) >= 2:
            town = parts[-2] if len(parts) >= 3 else parts[-1]

    # Build service cards with images + descriptions - rotate verified images by slug, no repeats within a demo
    used_images = set()
    cards = []
    for idx, svc in enumerate(services[:6]):
        tag, img, desc = get_service_meta(svc)
        key = "repairs"
        for candidate in ["mot", "servicing", "service", "tyre", "diagnostic", "engine", "suspension", "collection", "brake", "clutch"]:
            if candidate in svc.lower():
                key = {"service":"servicing", "diagnostic":"engine", "brake":"repairs", "clutch":"repairs"}.get(candidate, candidate)
                break
        img = pick_variant(key, slug or name, used_images, f"service-{idx}")
        used_images.add(img)
        cards.append(f"""        <div class="svc-card">
          <div class="svc-img" style="background-image:url('{img}')"></div>
          <div class="svc-body">
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
          <div class="about-img" style="background-image:url('{pick_variant('about', slug or name, used_images, 'about')}')"></div>
          <div class="about-text">
            <span class="eyebrow">About Us</span>
            <h2>Your local, independent garage</h2>
            <p>{about}</p>
            <a href="#contact" class="btn" style="margin-top:16px;">Get In Touch</a>
          </div>
        </div>
      </section>"""

    blog_cards = []
    for post in select_blog_posts(slug or name):
        blog_cards.append(f"""        <article class="blog-card">
          <div class="blog-img" style="background-image:url('{post['image']}')"></div>
          <div class="blog-body">
            <p class="blog-kicker">Advice</p>
            <h3>{post['title']}</h3>
            <h4>{post['subtitle']}</h4>
            <p>{post['excerpt']}</p>
            <a href="#" class="read-more" onclick="return false;">Read More</a>
          </div>
        </article>""")
    blog_html = f"""      <section id="blog" class="blog-sec">
        <div class="wrap">
          <span class="eyebrow" style="display:block;text-align:center;">Useful Guides</span>
          <h2 class="sec-title">Car Care Advice</h2>
          <div class="blog-grid">
{chr(10).join(blog_cards)}
          </div>
        </div>
      </section>"""

    email_html = f"<p><strong>Email:</strong> <a href='mailto:{email}' class='brand-link'>{email}</a></p>" if email else ""
    hours_html = f"<p><strong>Hours:</strong> {hours}</p>" if hours else ""
    map_q = location.replace(",", "+").replace(" ", "+") if location else name.replace(" ", "+")
    map_url = f"https://www.google.com/maps?q={map_q}&output=embed"
    posthog_html = posthog_head(slug, name)

    hero_image = pick_variant('hero', slug or name, used_images, 'hero')

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
    .hero-overlay {{position:absolute; inset:0; background:linear-gradient(rgba(0,0,0,.42),rgba(0,0,0,.52));}}
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
    .svc-body h3 {{font-size:1.05rem; margin:0 0 6px; color:var(--text);}}
    .svc-body p {{font-size:0.88rem; color:var(--muted); margin:0; line-height:1.5;}}

    .about-sec {{background:var(--card);}}
    .two-col {{display:grid; grid-template-columns:1fr 1fr; gap:48px; align-items:center;}}
    .about-img {{height:400px; background-size:cover; background-position:center; border-radius:14px;}}
    .about-text p {{font-size:1.1rem; color:var(--muted); margin-top:12px;}}

    .blog-sec {{background:var(--bg);}}
    .blog-grid {{display:grid; grid-template-columns:repeat(3,1fr); gap:24px;}}
    .blog-card {{background:var(--card); border-radius:14px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,.05); border:1px solid #eee; transition:transform .2s, box-shadow .2s, border-color .2s;}}
    .blog-card:hover {{transform:translateY(-5px); box-shadow:0 16px 34px rgba(0,0,0,.10); border-color:color-mix(in srgb, var(--b) 36%, #eee);}}
    .blog-img {{height:170px; background-size:cover; background-position:center; transition:transform .25s ease;}}
    .blog-card:hover .blog-img {{transform:scale(1.03);}}
    .blog-body {{padding:22px 24px 24px;}}
    .blog-kicker {{color:var(--b); font-weight:800; font-size:.72rem; text-transform:uppercase; letter-spacing:.12em; margin:0 0 6px;}}
    .blog-body h3 {{font-size:1.18rem; line-height:1.25; margin:0 0 8px; color:var(--text);}}
    .blog-body h4 {{font-size:.95rem; line-height:1.45; margin:0 0 10px; color:#444; font-weight:700;}}
    .blog-body p {{font-size:.9rem; color:var(--muted); margin:0 0 16px; line-height:1.55;}}
    .read-more {{display:inline-block; color:var(--b); font-weight:800; font-size:.9rem;}}
    .read-more:hover {{text-decoration:underline;}}

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

    footer {{background:var(--d); color:#888; padding:32px 24px 80px; text-align:center; font-size:0.88rem;}}

    /* Buy bar */
    .buy-bar {{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:2px solid var(--b);padding:14px 24px;z-index:100;display:flex;justify-content:center;align-items:center;gap:20px;box-shadow:0 -4px 20px rgba(0,0,0,.1);flex-wrap:wrap}}
    .buy-bar span {{font-weight:600;color:#1a1a1a;font-size:.95rem}}
    .btn-o {{background:transparent;color:var(--b);padding:12px 28px;border-radius:8px;font-weight:600;display:inline-block;border:2px solid var(--b);cursor:pointer;font-size:.95rem}}
    .btn-o:hover {{background:var(--b);color:#fff}}
    .tier-panel {{display:none;position:fixed;bottom:0;left:0;right:0;background:#f8f8f8;border-top:3px solid var(--b);padding:40px 24px 100px;z-index:90;max-height:90vh;overflow-y:auto;box-shadow:0 -8px 40px rgba(0,0,0,.15)}}
    .tier-panel.active {{display:block}}
    .tiers {{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;max-width:900px;margin:0 auto}}
    .tier {{background:#fff;border:2px solid #e5e5e5;border-radius:12px;padding:28px;text-align:center;position:relative;display:flex;flex-direction:column}}
    .tier.featured {{border-color:var(--b);box-shadow:0 8px 24px rgba(0,0,0,.08)}}
    .tier-badge {{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--b);color:#fff;padding:4px 16px;border-radius:50px;font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em}}
    .tier h4 {{font-size:1.05rem;font-weight:700;color:#1a1a1a;margin:0 0 4px}}
    .tier .price {{font-size:2.2rem;font-weight:800;color:#1a1a1a;margin:0}}
    .tier .price span {{font-size:.85rem;font-weight:500;color:#888}}
    .tier ul {{list-style:none;padding:0;margin:0 0 20px;text-align:left;flex-grow:1}}
    .tier ul li {{padding:5px 0;border-bottom:1px solid #f0f0f0;color:#444;font-size:.85rem}}
    .tier .btn {{display:block;width:100%;padding:12px;border-radius:6px;font-weight:600;text-align:center;margin-bottom:8px}}
    .confirm-overlay {{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:200;align-items:center;justify-content:center}}
    .confirm-overlay.active {{display:flex}}
    .confirm-box {{background:#fff;border-radius:12px;padding:32px;max-width:420px;width:90%;text-align:center}}

    @media(max-width:768px) {{
      .nav-links a {{display:none;}}
      .nav-links .btn {{display:inline-block;}}
      .hero h1 {{font-size:2.1rem;}}
      .two-col, .contact-grid {{grid-template-columns:1fr;}}
      .blog-grid {{grid-template-columns:1fr;}}
      .about-img {{height:240px;}}
      .hero {{min-height:420px;}}
      .hero-content {{padding:60px 24px;}}
    }}
  </style>
{posthog_html}
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
    <img class="hero-bg" src="{hero_image}" alt="Garage workshop">
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

{blog_html}

  <section id="contact" class="wrap">
    <span class="eyebrow" style="display:block;text-align:center;">Get In Touch</span>
    <h2 class="sec-title">Book Your Vehicle In</h2>
    <div class="contact-grid">
      <div>
        <form id="cf" action="https://formsubmit.co/ajax/{form_email}" method="POST">
          <input type="hidden" name="_subject" value="New enquiry from {name} demo site">
          <input type="hidden" name="_template" value="table">
          <input type="text" name="_honey" style="display:none">
          <div class="form-grp">
            <label>Your Name</label>
            <input type="text" name="name" required placeholder="John Smith">
          </div>
          <div class="form-grp">
            <label>Email</label>
            <input type="email" name="email" required placeholder="you@example.com">
          </div>
          <div class="form-grp">
            <label>Phone</label>
            <input type="tel" name="phone" placeholder="Your phone number">
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

  <div class="buy-bar" id="bb">
    <span>Want this site for your garage?</span>
    <button class="btn" onclick="showTiers()">Get This Site - from £149</button>
    <button class="btn-o" onclick="showNI()">Not For Me</button>
  </div>

  <div class="tier-panel" id="tp">
    <div style="position:relative;max-width:900px;margin:0 auto">
      <button style="position:absolute;top:0;right:0;font-size:1.5rem;color:#999;cursor:pointer;background:none;border:none" onclick="hideTiers()">&times;</button>
      <h3 style="text-align:center;font-size:1.5rem;margin:0 0 8px">Get Your Site</h3>
      <p style="text-align:center;color:#666;margin:0 0 32px">Pick the package that fits. No monthly fees. No lock-in.</p>
      <div class="tiers">
        <div class="tier">
          <h4>Buy Outright</h4>
          <p class="price">£149 <span>one-time</span></p>
          <ul>
            <li>Complete page deployed live</li>
            <li>Free Vercel account setup</li>
            <li>Ownership transferred to you</li>
            <li>Add your own custom domain</li>
          </ul>
          <a href="https://buy.stripe.com/14AaENc4oeYBgfk26R5EY0f?client_reference_id={slug}" class="btn" onclick="trackEvent('buy_149_clicked')">Buy - £149</a>
        </div>
        <div class="tier featured">
          <div class="tier-badge">Popular</div>
          <h4>Hosted + Edits</h4>
          <p class="price">£399 <span>one-time</span></p>
          <ul>
            <li>Live deployment to Vercel</li>
            <li>12 months hosting included</li>
            <li>2 rounds of edits included</li>
            <li>Email support</li>
          </ul>
          <a href="https://buy.stripe.com/fZu4gpecw2bPbZ4dPz5EY0g?client_reference_id={slug}" class="btn" onclick="trackEvent('hosted_399_clicked')">Buy - £399</a>
        </div>
        <div class="tier">
          <h4>Want More Than a Page?</h4>
          <p style="color:#666;font-size:0.95rem;line-height:1.45;margin:0 0 20px;">This is a single page. We build the full thing.</p>
          <ul>
            <li>Full multi-page website</li>
            <li>Database-driven: bookings, enquiries, CRM</li>
            <li>Automated lead follow-up</li>
            <li>Built to grow with your business</li>
          </ul>
          <a href="https://propagate.media/web-design" target="_blank" rel="noopener" class="btn" onclick="trackEvent('more_than_page_clicked')">See What We Do</a>
        </div>
      </div>
      <p style="text-align:center;color:#666;margin:24px 0 0;font-size:0.9rem;">Swapping the image for your own is included in any purchase, free of charge.</p>
      <div style="text-align:center;color:#444;margin:18px auto 0;font-size:0.95rem;line-height:1.6;max-width:620px;">
        <strong>Contact Us:</strong> <a href="tel:07400338941" style="color:var(--b);font-weight:700;">07400 33 8941</a><br>
        If you're looking for something different or would like to ask us anything, email <a href="mailto:hello@propagate.media" style="color:var(--b);font-weight:700;">hello@propagate.media</a>
      </div>
    </div>
  </div>

  <div class="confirm-overlay" id="co">
    <div class="confirm-box">
      <h3>Remove This Demo?</h3>
      <p>If this isn't for you, no problem. This demo page for {name} will be taken down within 12 hours.</p>
      <div style="display:flex;gap:12px;justify-content:center">
        <button class="btn-o" onclick="hideNI()">Keep It</button>
        <button class="btn" onclick="doDel()" style="background:#666">Remove It</button>
      </div>
    </div>
  </div>

  <script>
    function trackEvent(eventName, props){{
      try {{
        if (window.posthog && typeof window.posthog.capture === 'function') {{
          window.posthog.capture(eventName, Object.assign({{lead_slug:'{slug}', business_name:'{name}'}}, props || {{}}));
        }}
      }} catch(e) {{}}
    }}
    function showTiers(){{trackEvent('buy_bar_clicked');trackEvent('pricing_opened');document.getElementById('tp').classList.add('active');document.getElementById('bb').style.display='none'}}
    function hideTiers(){{document.getElementById('tp').classList.remove('active');document.getElementById('bb').style.display='flex'}}
    function showNI(){{trackEvent('not_for_me_clicked');document.getElementById('co').classList.add('active')}}
    function hideNI(){{document.getElementById('co').classList.remove('active')}}

    // Prospect declined - notify FreshSites via Web3Forms, then confirm to the visitor.
    async function doDel(){{
      trackEvent('demo_remove_confirmed');
      var box = document.querySelector('#co .confirm-box');
      box.innerHTML = '<h3>Thanks for letting us know</h3><p>This demo will be removed within 12 hours. If you change your mind, just reply to our email.</p>';
      try {{
        await fetch('https://formsubmit.co/ajax/{form_email}', {{
          method: 'POST',
          headers: {{'Content-Type':'application/json'}},
          body: JSON.stringify({{
            _subject: 'DELETE REQUEST: {name} declined their demo',
            demo: '{slug}',
            live_page: 'https://propagatemedia.github.io/freshsites-outreach/demos/{slug}.html',
            action_needed: 'Prospect clicked Not for me. Remove this demo within 12 hours.'
          }})
        }});
      }} catch(e) {{}}
      document.getElementById('bb').style.display='none';
      document.getElementById('tp').classList.remove('active');
      setTimeout(function(){{document.getElementById('co').classList.remove('active');}}, 4000);
    }}

    // Contact form - submit to FormSubmit (free, no key) via fetch, show inline success.
    var contactFormStarted = false;
    document.getElementById('cf').addEventListener('input', function(){{
      if (!contactFormStarted) {{ contactFormStarted = true; trackEvent('contact_form_started'); }}
    }});
    document.getElementById('cf').addEventListener('submit', async function(e){{
      e.preventDefault();
      trackEvent('contact_form_submitted');
      var form = e.target;
      var btn = form.querySelector('button[type=submit]');
      var orig = btn.textContent;
      btn.textContent = 'Sending...'; btn.disabled = true;
      var payload = {{}};
      new FormData(form).forEach(function(v,k){{ payload[k]=v; }});
      try {{
        var resp = await fetch(form.action, {{
          method:'POST',
          headers: {{'Content-Type':'application/json','Accept':'application/json'}},
          body: JSON.stringify(payload)
        }});
        var data = await resp.json().catch(function(){{return {{}};}});
        // FormSubmit returns success:"true" on delivery. Anything else (incl. first-time
        // activation) we still treat as "received" for the visitor - the enquiry is logged.
        form.style.display='none';
        document.getElementById('sf').style.display='block';
      }} catch(err) {{
        btn.textContent = orig; btn.disabled = false;
        alert('Sorry, something went wrong. Please call us on the number above.');
      }}
    }});
    document.getElementById('co').addEventListener('click',function(e){{if(e.target===this)hideNI()}});
    document.getElementById('tp').addEventListener('click',function(e){{if(e.target===this)hideTiers()}})
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
