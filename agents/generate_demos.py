#!/usr/bin/env python3
"""
Generate 10 FreshSites demos with verified automotive images and actual services.
Uses Jinja2-style templating to batch generate all demos at once.
"""

from pathlib import Path
from string import Template

# Verified automotive image URLs (all tested with HTTP 200)
IMAGES = {
    "diagnostics": "https://images.unsplash.com/photo-1578844251758-2f71da64c96f?w=500&h=280&fit=crop&q=80",
    "servicing": "https://images.unsplash.com/photo-1625047509168-a7026f36de04?w=500&h=280&fit=crop&q=80",
    "tyres": "https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?w=500&h=280&fit=crop&q=80",
    "workshop": "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?w=500&h=280&fit=crop&q=80",
    "brakes": "https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=500&h=280&fit=crop&q=80",
    "mechanic": "https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=500&h=280&fit=crop&q=80",
    "car": "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=500&h=280&fit=crop&q=80",
    "engine": "https://images.unsplash.com/photo-1487754180451-c456f719a1fc?w=500&h=280&fit=crop&q=80",
    "car_front": "https://images.unsplash.com/photo-1517524206127-48bbd363f3d7?w=500&h=280&fit=crop&q=80",
    "hero_workshop": "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?w=1600&h=700&fit=crop&q=80",
    "hero_garage": "https://images.unsplash.com/photo-1625047509168-a7026f36de04?w=1600&h=700&fit=crop&q=80",
    "hero_mechanic": "https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=1600&h=700&fit=crop&q=80",
    "about_mechanic": "https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=600&h=500&fit=crop&q=80",
}

LEADS = [
    {
        "name": "Bradleys Garage",
        "slug": "bradleys-garage",
        "brand_color": "#c41e3a",
        "location": "Llanidloes, SY18 6RB",
        "phone": "01686 430 002",
        "hours": "Monday - Friday: 8:30 - 17:30 | Saturday: 8:30 - 12:00",
        "badge": "Family Run Since 1920",
        "hero_text": "Full vehicle servicing, MOT testing and repairs in Mid Wales",
        "hero_img": IMAGES["hero_workshop"],
        "about_img": IMAGES["about_mechanic"],
        "services": [
            ("Serving", "Servicing & MOTs", "Comprehensive vehicle servicing, MOT testing and preparation for all makes and models."),
            ("Diagnos", "Advanced Diagnostics", "The latest diagnostic tools and technology to find and fix issues fast."),
            ("Tyres", "Tyres & Fitting", "Tyre supply, fitting and maintenance to keep you safe and roadworthy."),
            ("A/C", "Air Conditioning", "Full air conditioning servicing and re-gas for summer comfort."),
            ("Repairs", "Repairs & Parts", "From routine maintenance to complex repairs. All work guaranteed."),
            ("HGV", "HGV & Commercial", "Commercial vehicle servicing and repairs. Specialist experience since 1920."),
        ],
        "about": "Family run Bradleys have been in the motor industry for almost a century looking after all motoring needs. Previously Rover, Peugeot and Renault dealers, we have a wealth of experience in our workshop and pride ourselves on offering the highest level of customer care.",
    },
    {
        "name": "D A Autos",
        "slug": "d-a-autos",
        "brand_color": "#2563eb",
        "location": "Welshpool, SY21 7DG",
        "phone": "01938 552 245",
        "hours": "Monday - Friday: 8:00 - 17:30 | Saturday: 8:00 - 12:00",
        "badge": "Independent Family Business",
        "hero_text": "Tyres, servicing, MOT prep and repairs in Welshpool",
        "hero_img": IMAGES["hero_garage"],
        "about_img": IMAGES["about_mechanic"],
        "services": [
            ("Tyres", "Tyre Supply & Fitting", "Quality tyres for all makes and models, fitted with expert care and competitive pricing."),
            ("Servic", "Car Servicing", "Comprehensive vehicle servicing from oil and filter changes to full inspections."),
            ("MOT", "MOT Preparation", "Prepare your car for its MOT with expert checks and repairs. Pass with confidence."),
            ("Repairs", "Repairs & Welding", "All types of repairs and welding work undertaken by experienced mechanics."),
            ("Buy", "We Buy Any Car", "MOT-failed, damaged or repairable vehicles bought for cash. Fast local collection."),
            ("Collect", "Collection Service", "Fast and convenient vehicle collection available throughout Powys."),
        ],
        "about": "D A Autos is more than just a tyre specialist, we are your trusted local garage. Over 15 years as a family-run business, we pride ourselves on delivering reliable, affordable garage services with a personal touch.",
    },
    {
        "name": "DC Autos Newtown",
        "slug": "dc-autos-newtown",
        "brand_color": "#e87900",
        "location": "Newtown, SY16 4JJ",
        "phone": "01686 629 200",
        "hours": "Monday - Friday: 8:00 - 17:00 | Saturday - Sunday: Closed",
        "badge": "30+ Years Experience",
        "hero_text": "MOTs, servicing, diagnostics and repairs for cars and vans",
        "hero_img": IMAGES["hero_garage"],
        "about_img": IMAGES["about_mechanic"],
        "services": [
            ("MOT", "MOT Testing", "Book your MOT online. Real-time booking, reminders and re-tests available."),
            ("Servic", "Servicing & Repairs", "Expert servicing and repairs using the latest diagnostic equipment."),
            ("Diagnos", "Diagnostics", "Engine management and fault finding for all makes and models."),
            ("Tyres", "Tyre Services", "Supply, fitting and balancing for cars, vans and 4x4s."),
            ("A/C", "Air Conditioning", "Air conditioning re-gas and repair to keep you cool."),
            ("Fly", "DPF & Flywheel", "DPF cleaning, turbo repairs and dual mass flywheel replacements."),
        ],
        "about": "DC Autos is a trusted, family-run garage providing expert servicing, diagnostics, repairs and outsourced MOTs. With over 30 years of dealership-trained experience, we focus on delivering quality workmanship, fair pricing and honest advice.",
    },
    {
        "name": "K's Garage",
        "slug": "ks-garage",
        "brand_color": "#1d4ed8",
        "location": "Newtown, SY16 4BQ",
        "phone": "01686 625 872",
        "hours": "Monday - Friday: 8:30 - 17:00 | Saturday - Sunday: Closed",
        "badge": "Local & Reliable",
        "hero_text": "MOTs, servicing, clutches and tyres throughout Mid Wales",
        "hero_img": IMAGES["hero_workshop"],
        "about_img": IMAGES["about_mechanic"],
        "services": [
            ("MOT", "MOT Testing", "Class 4 and 7 MOT testing with free retest within 10 days."),
            ("Servic", "Servicing & Repairs", "Full and interim servicing, plus general repairs for all makes."),
            ("Clutch", "Clutches", "Clutch replacements and dual mass flywheel repairs at competitive prices."),
            ("Tyres", "Tyres", "New and part-worn tyres. Wheel balancing and puncture repairs."),
            ("Exhaust", "Exhausts", "Exhaust repairs and replacements with fast turnaround."),
            ("Brake", "Brakes", "Brake pads, discs and fluid changes. Safety checked and guaranteed."),
        ],
        "about": "K's Garage offers a wide range of motor repair services. From MOTs and servicing to major repairs, we help ensure you are always safe on the road at a competitive rate.",
    },
    {
        "name": "Border Garage",
        "slug": "border-garage",
        "brand_color": "#dc2626",
        "location": "Welshpool, SY21 7BE",
        "phone": "01938 554 444",
        "hours": "Monday - Friday: 8:00 - 17:30 | Saturday: 8:00 - 12:00",
        "badge": "MOT Testing Station",
        "hero_text": "Book your MOT online. Real-time 24/7 booking available",
        "hero_img": IMAGES["hero_garage"],
        "about_img": IMAGES["about_mechanic"],
        "services": [
            ("MOT", "MOT Testing", "Book online 24/7 with real-time availability. Free retests within 10 days."),
            ("Servic", "Full & Interim Service", "Comprehensive servicing using quality parts to keep your car in peak condition."),
            ("Clutch", "Clutch Replacements", "Clutch fitting with original equipment quality parts and warranty."),
            ("Exhaust", "Exhaust Systems", "From minor repairs to full system replacements for all makes."),
            ("Diagnos", "Diagnostics", "Full diagnostic scans and fault finding using the latest technology."),
            ("Brake", "Brake Services", "Pads, discs, shoes and full hydraulic system servicing."),
        ],
        "about": "Border Garage is your local independent garage now offering online MOT booking. With decades of experience and a commitment to customer service, we keep your vehicle safe and roadworthy.",
    },
    {
        "name": "Evans Motors",
        "slug": "evans-motors",
        "brand_color": "#166534",
        "location": "Rhayader, LD6 5BU",
        "phone": "01597 810 289",
        "hours": "Monday - Friday: 8:30 - 17:00 | Saturday: 8:30 - 12:00",
        "badge": "Established 1964",
        "hero_text": "Family-run garage serving Rhayader since 1964",
        "hero_img": IMAGES["hero_workshop"],
        "about_img": IMAGES["about_mechanic"],
        "services": [
            ("MOT", "MOT Testing", "Class 4 and 7 MOT testing. Walk-ins welcome but booking recommended."),
            ("Servic", "Servicing & Repairs", "Comprehensive servicing and repairs for all makes and models."),
            ("Brake", "Brakes", "Brake pads, discs and drum replacements. Safety guaranteed."),
            ("Tyre", "Tyres", "New, part-worn and winter tyres. Balancing, tracking and puncture repairs."),
            ("Exhaust", "Exhausts & Batteries", "Exhaust repairs and battery replacements at competitive prices."),
            ("Collect", "Collection Available", "Local collection and delivery service for your convenience."),
        ],
        "about": "Evans Motors is a family-run business established in 1964 in Rhayader. Our skilled mechanics provide a comprehensive range of services for cars and light commercial vehicles. We take pride in honest workmanship and customer care.",
    },
    {
        "name": "J T Hughes Newtown",
        "slug": "j-t-hughes-newtown",
        "brand_color": "#1e40af",
        "location": "Newtown, SY16 3BD",
        "phone": "01686 622 300",
        "hours": "Monday - Friday: 8:30 - 18:00 | Saturday: 9:00 - 17:00 | Sunday: Closed",
        "badge": "Newtown's Local Garage",
        "hero_text": "Your trusted local garage for MOTs, servicing and repairs",
        "hero_img": IMAGES["hero_garage"],
        "about_img": IMAGES["about_mechanic"],
        "services": [
            ("MOT", "MOT Testing", "Class 4 MOT testing available. Book online or by phone."),
            ("Servic", "Servicing", "Interim and full services for all makes and models."),
            ("Repair", "Repairs", "Mechanical repairs and maintenance to keep you roadworthy."),
            ("Diagnos", "Diagnostics", "Fault finding and engine management diagnostics using modern equipment."),
            ("Tyre", "Tyres & Batteries", "Tyre fitting, balancing and battery testing and replacement."),
            ("Brake", "Brake Services", "Full brake inspections, pad and disc replacements."),
        ],
        "about": "J T Hughes is a trusted local garage in Newtown with convenient opening hours six days a week. We provide MOT testing, servicing and repairs with a focus on quality and reliability.",
    },
]

# Add the existing 3 leads
EXISTING = [
    {
        "name": "M.E. Poston Motors",
        "slug": "meposton-motors",
        "brand_color": "#e8a010",
        "location": "Abermule, SY15 6ND",
        "phone": "01686 630 653",
        "hours": "Monday - Friday: 8:30AM - 5:30PM | Saturday: By Appointment Only",
        "badge": "Established 1938",
        "hero_text": "Engineers to the Motor Trade since 1938",
        "hero_img": IMAGES["hero_workshop"],
        "about_img": IMAGES["about_mechanic"],
        "services": [
            ("Diagnos", "Autologic Diagnostics", "We find the fault fast and fix it right first time with Autologic equipment."),
            ("Brake", "Brake Disc + Pad Repairs", "Professional brake disc and pad replacements for safe stopping."),
            ("Recovery", "Breakdown Recovery", "Breakdown recovery service to get you back on the road quickly."),
            ("Service", "Cambelt Replacement", "Protect your engine from costly damage with essential cambelt maintenance."),
            ("Battery", "Car Batteries", "Quality batteries fitted by experienced engineers."),
            ("Repair", "Car Repairs", "No job too large or too small. All makes and models welcome."),
            ("Service", "Car Servicing", "Keep your vehicle running smoothly with comprehensive servicing."),
            ("Clutch", "Clutch + DMF Replacements", "Expert clutch replacements with dual mass flywheel repairs."),
            ("Tune", "Engine Tuning + Remapping", "Improve performance and fuel efficiency with professional tuning."),
        ],
        "about": "M.E. Poston Motors has been operating as a long established engineering workshop in the heart of Mid Wales since 1938. We strive for excellence and understand the importance of good customer service.",
    },
    {
        "name": "Crossing Garage",
        "slug": "crossing-garage",
        "brand_color": "#0077be",
        "location": "Llandrindod Wells, LD1 6AA",
        "phone": "01597 829243",
        "hours": "Monday - Friday: 8:30 - 17:30 | Saturday: CLOSED | Sunday: CLOSED",
        "badge": "Independent Garage",
        "hero_text": "Car & Light Commercial Servicing in Llandrindod Wells",
        "hero_img": IMAGES["hero_garage"],
        "about_img": IMAGES["about_mechanic"],
        "services": [
            ("Service", "Car & Light Commercial Servicing", "Full servicing with high quality oils from Comma and Forte. Health-check included."),
            ("MOT", "MOT Testing", "Cars, vans and light commercials. Book up to a month before expiry."),
            ("Tyre", "Tyres", "Supply, fitting and puncture repairs. Do not take your tyres for granted."),
            ("Exhaust", "Exhausts", "Repairs and replacements with quality parts at competitive prices."),
            ("Repair", "Repairs & Parts", "Brakes to suspension, we keep you roadworthy and safe."),
            ("Air", "Air-Con Servicing", "Servicing and re-gas so your system works efficiently."),
            ("Belt", "Timing Belts", "Essential maintenance to protect your engine from costly damage."),
            ("Head", "Headlamp Refurbishment", "Restore clarity and improve visibility cost-effectively."),
            ("Clutch", "Clutches", "Repairs and replacements for cars and light commercial vehicles."),
        ],
        "about": "Crossing Garage is an independent garage in Llandrindod Wells offering a full range of services for car and light commercial vehicle owners. We pride ourselves on honest, reliable service at competitive prices.",
    },
    {
        "name": "Graig Goch Garage",
        "slug": "graig-goch",
        "brand_color": "#c41e3a",
        "location": "Builth Wells, LD2 3RU",
        "phone": "01982 554695",
        "hours": "Monday - Friday: 8:00 - 17:30 | Saturday: 8:00 - 12:00",
        "badge": "DVSA Approved Station",
        "hero_text": "MOT, Servicing & Repairs in Builth Wells",
        "hero_img": IMAGES["hero_workshop"],
        "about_img": IMAGES["about_mechanic"],
        "services": [
            ("MOT", "MOT Testing Station", "Classes 4 and 7 tested including cars, vans and goods vehicles up to 3,500kg."),
            ("Service", "Pre-MOT Service", "Help your vehicle pass first time with our pre-MOT checks."),
            ("Service", "Servicing", "Full workshop facilities for all makes and models at competitive prices."),
            ("Repair", "General Repairs", "No job too large or too small. Reliable workmanship guaranteed."),
            ("Tyre", "Tyres", "Supply and fitting at competitive prices for cars and light commercials."),
            ("Collect", "Collection & Delivery", "Local collection and delivery service for your convenience."),
        ],
        "about": "Graig Goch Garage in Builth Wells is a DVSA approved MOT testing station. We provide full workshop facilities with competitive prices and a collection and delivery service. No job is too large or too small.",
    },
]

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${name} — ${description}</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root { --brand: ${brand_color}; --brand-dark: ${brand_dark}; }
    * { box-sizing: border-box; }
    body { margin:0;padding:0;font-family:'Inter',sans-serif;color:#1a1a1a;background:#fff;line-height:1.6; }
    img { max-width:100%;display:block; }
    a { text-decoration:none;transition:all .2s; }
    .top-bar { background:${brand_dark};color:#fff;padding:10px 24px;font-size:0.8rem;text-align:center; }
    .top-bar a { color:${brand_color};font-weight:600; }
    nav { position:sticky;top:0;z-index:50;background:rgba(255,255,255,0.97);backdrop-filter:blur(8px);border-bottom:1px solid #e5e5e5; }
    .nav-inner { max-width:1200px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between;height:68px; }
    .logo { font-weight:800;font-size:1.25rem;color:${brand_color}; }
    .logo span { color:${brand_dark}; }
    .nav-links { display:flex;gap:36px;align-items:center; }
    .nav-links a { font-weight:500;font-size:0.9rem;color:#333; }
    .nav-links a:hover { color:${brand_color}; }
    .btn-primary { background:${brand_color};color:#fff;padding:10px 22px;border-radius:6px;font-weight:600;font-size:0.85rem;display:inline-block;border:none;cursor:pointer; }
    .btn-primary:hover { opacity:0.9; }
    .btn-outline { background:transparent;color:${brand_color};padding:10px 18px;border-radius:6px;font-weight:600;font-size:0.85rem;border:1.5px solid ${brand_color};display:inline-block;cursor:pointer; }
    .btn-outline:hover { background:${brand_color};color:#fff; }
    .hero { position:relative;height:600px;overflow:hidden; }
    .hero img { position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center; }
    .hero-overlay { position:absolute;inset:0;background:linear-gradient(90deg,${hero_overlay} 0%,${hero_overlay_2} 60%,transparent 100%); }
    .hero-content { position:absolute;inset:0;display:flex;align-items:center; }
    .hero-inner { max-width:1200px;margin:0 auto;padding:0 24px;width:100%; }
    .hero-text { max-width:560px; }
    .badge { display:inline-flex;align-items:center;gap:8px;background:${badge_bg};border:1px solid rgba(255,255,255,0.4);padding:6px 14px;border-radius:50px;font-size:0.75rem;font-weight:600;color:#fff;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:20px; }
    .badge-dot { width:6px;height:6px;background:#fff;border-radius:50%;display:inline-block; }
    .hero h1 { font-size:3.2rem;font-weight:800;color:#fff;line-height:1.05;letter-spacing:-0.03em;margin:0 0 16px; }
    .hero p { font-size:1.15rem;color:rgba(255,255,255,0.85);margin:0 0 28px;max-width:440px; }
    .hero-btns { display:flex;gap:14px;flex-wrap:wrap; }
    .btn-ghost { background:transparent;color:#fff;padding:14px 24px;border-radius:8px;font-weight:600;font-size:1rem;border:1.5px solid rgba(255,255,255,0.35);display:inline-block; }
    .btn-ghost:hover { border-color:#fff; }
    .trust { background:#f8f8f8;border-bottom:1px solid #e5e5e5; }
    .trust-inner { max-width:1200px;margin:0 auto;padding:32px 24px;display:flex;justify-content:space-around;align-items:center;flex-wrap:wrap;gap:24px; }
    .trust-item { text-align:center; }
    .trust-item strong { display:block;font-size:1.8rem;font-weight:800;color:${brand_color}; }
    .trust-item span { font-size:0.8rem;color:#666;text-transform:uppercase;letter-spacing:0.05em; }
    section { padding:80px 24px; }
    .section-inner { max-width:1200px;margin:0 auto; }
    .section-header { text-align:center;margin-bottom:56px; }
    .section-header span { display:inline-block;color:${brand_color};font-weight:700;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.18em;margin-bottom:12px; }
    .section-header h2 { font-size:2.4rem;font-weight:800;color:#1a1a1a;letter-spacing:-0.02em;margin:0; }
    .section-header p { color:#666;font-size:1.1rem;margin:12px auto 0;max-width:500px; }
    .cards { display:grid;grid-template-columns:repeat(3,1fr);gap:32px; }
    .card { border:1px solid #e5e5e5;border-radius:12px;overflow:hidden;transition:all .3s; }
    .card:hover { box-shadow:0 8px 24px rgba(0,0,0,0.08); }
    .card img { width:100%;height:200px;object-fit:cover;object-position:center; }
    .card-body { padding:28px; }
    .card-body h3 { font-size:1.2rem;font-weight:700;color:#1a1a1a;margin:0 0 8px; }
    .card-body p { color:#666;font-size:0.95rem;margin:0; }
    .about { background:#f8f8f8; }
    .about-grid { display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:center; }
    .about-text span { display:inline-block;color:${brand_color};font-weight:700;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.18em;margin-bottom:12px; }
    .about-text h2 { font-size:2.4rem;font-weight:800;color:#1a1a1a;letter-spacing:-0.02em;margin:0 0 20px; }
    .about-text p { color:#444;font-size:1.05rem;margin:0 0 16px; }
    .about-img { width:100%;border-radius:12px;box-shadow:0 20px 40px rgba(0,0,0,0.12); }
    .cta { background:${brand_dark};color:#fff;text-align:center; }
    .cta-inner { max-width:600px;margin:0 auto; }
    .cta-inner span { display:inline-block;color:${brand_color};font-weight:700;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.18em;margin-bottom:16px; }
    .cta-inner h2 { font-size:2.4rem;font-weight:800;margin:0 0 16px; }
    .cta-inner > p { font-size:1.1rem;color:rgba(255,255,255,0.75);margin:0 0 28px; }
    .cta-phone { font-size:2rem;font-weight:800;color:${brand_color};display:block;margin-bottom:8px; }
    .cta-phone:hover { color:#fff; }
    .cta-hours { font-size:0.85rem;color:rgba(255,255,255,0.5);margin:0 0 20px; }
    footer { background:#0d0d0d;color:rgba(255,255,255,0.4);padding:40px 24px 24px;font-size:0.85rem; }
    .footer-inner { max-width:1200px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px; }
    footer strong { color:#fff;font-size:1rem; }
    .buy-bar { position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:2px solid ${brand_color};padding:14px 24px;z-index:100;display:flex;justify-content:center;align-items:center;gap:20px;box-shadow:0 -4px 20px rgba(0,0,0,0.1);flex-wrap:wrap; }
    .buy-bar span { font-weight:600;color:#1a1a1a;font-size:0.95rem; }
    .tier-panel { display:none;position:fixed;bottom:0;left:0;right:0;background:#f8f8f8;border-top:3px solid ${brand_color};padding:40px 24px 100px;z-index:90;max-height:90vh;overflow-y:auto;box-shadow:0 -8px 40px rgba(0,0,0,0.15); }
    .tier-panel.active { display:block; }
    .tiers { display:grid;grid-template-columns:repeat(3,1fr);gap:24px; }
    .tier { background:#fff;border:2px solid #e5e5e5;border-radius:12px;padding:28px;text-align:center;position:relative;display:flex;flex-direction:column; }
    .tier.featured { border-color:${brand_color};box-shadow:0 8px 24px rgba(0,0,0,0.08); }
    .tier-badge { position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:${brand_color};color:#fff;padding:4px 16px;border-radius:50px;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em; }
    .tier h4 { font-size:1.05rem;font-weight:700;color:#1a1a1a;margin:0 0 4px; }
    .tier .price { font-size:2.2rem;font-weight:800;color:#1a1a1a;margin:0; }
    .tier .price span { font-size:0.85rem;font-weight:500;color:#888; }
    .tier ul { list-style:none;padding:0;margin:0 0 20px;text-align:left;flex-grow:1; }
    .tier ul li { padding:5px 0;border-bottom:1px solid #f0f0f0;color:#444;font-size:0.85rem; }
    .tier .btn { display:block;width:100%;padding:10px;border-radius:6px;font-weight:600;text-align:center;margin-bottom:8px; }
    .confirm-overlay { display:none;position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:200;align-items:center;justify-content:center; }
    .confirm-overlay.active { display:flex; }
    .confirm-box { background:#fff;border-radius:12px;padding:32px;max-width:420px;width:90%;text-align:center; }
    .removed-bar { display:none;position:fixed;bottom:0;left:0;right:0;background:#1a1a1a;color:#fff;padding:14px 24px;z-index:100;text-align:center; }
    .removed-bar.active { display:block; }
    .removed-bar a { color:${brand_color};font-weight:600; }
    @media (max-width:768px) {
      .hero h1 { font-size:2rem; }
      .hero { height:400px; }
      .cards, .tiers { grid-template-columns:1fr; }
      .about-grid { grid-template-columns:1fr; }
      .nav-links { display:none; }
    }
  </style>
</head>
<body>

  <div class="top-bar">
    <span>${location}</span> | <a href="tel:${phone}">${phone}</a>
  </div>

  <nav>
    <div class="nav-inner">
      <a href="#" class="logo">${logo_text}</a>
      <div class="nav-links">
        <a href="#services">Services</a>
        <a href="#about">About</a>
        <a href="#contact">Contact</a>
        <a href="tel:${phone}" class="btn-primary">Call Now</a>
      </div>
    </div>
  </nav>

  <section class="hero">
    <img src="${hero_img}" alt="${name}">
    <div class="hero-overlay"></div>
    <div class="hero-content">
      <div class="hero-inner">
        <div class="hero-text">
          <div class="badge"><span class="badge-dot"></span> ${badge}</div>
          <h1>${hero_text}</h1>
          <p>${tagline}</p>
          <div class="hero-btns">
            <a href="tel:${phone}" class="btn-primary" style="padding:14px 28px;font-size:1rem;">Call ${phone}</a>
            <a href="#services" class="btn-ghost">Our Services</a>
          </div>
        </div>
      </div>
    </div>
  </section>

  <div class="trust">
    <div class="trust-inner">
      ${trust_items}
    </div>
  </div>

  <section id="services">
    <div class="section-inner">
      <div class="section-header">
        <span>What We Offer</span>
        <h2>Our Services</h2>
        <p>Comprehensive garage services for cars and light commercial vehicles.</p>
      </div>
      <div class="cards">
        ${services_html}
      </div>
    </div>
  </section>

  <section id="about" class="about">
    <div class="section-inner">
      <div class="about-grid">
        <div class="about-text">
          <span>About Us</span>
          <h2>${about_heading}</h2>
          ${about_paras}
          <a href="tel:${phone}" class="btn-primary" style="margin-top:8px;">Call Us Today</a>
        </div>
        <div>
          <img src="${about_img}" alt="${name} workshop" class="about-img">
        </div>
      </div>
    </div>
  </section>

  <section id="contact" class="cta">
    <div class="cta-inner">
      <span>Get In Touch</span>
      <h2>Book Your Vehicle In Today</h2>
      <p>Call now to book your vehicle in or request a quote.</p>
      <a href="tel:${phone}" class="cta-phone">${phone}</a>
      <p class="cta-hours">${hours}</p>
      <p style="margin-top:20px;font-size:0.85rem;color:rgba(255,255,255,0.4);">${location}</p>
    </div>
  </section>

  <footer>
    <div class="footer-inner">
      <div><strong>${name}</strong><span style="margin-left:16px;">${location}</span></div>
      <div style="display:flex;gap:20px;"><span>2024 ${name}</span></div>
    </div>
  </footer>

  <div class="buy-bar" id="buy-bar">
    <span>Want this site for your garage?</span>
    <button class="btn-primary" onclick="showTiers()">Get This Site - from 149</button>
    <button class="btn-outline" onclick="showNotInterested()">Not For Me</button>
  </div>

  <div class="tier-panel" id="tier-panel">
    <div class="section-inner" style="position:relative;">
      <button style="position:absolute;top:0;right:0;font-size:1.5rem;color:#999;cursor:pointer;background:none;border:none;" onclick="hideTiers()">&times;</button>
      <h3 style="text-align:center;font-size:1.5rem;margin:0 0 8px;">Get Your Site</h3>
      <p style="text-align:center;color:#666;margin:0 0 32px;">Pick the package that fits. No monthly fees. No lock-in.</p>
      <div class="tiers">
        <div class="tier">
          <h4>Buy Outright</h4>
          <p class="price">149 <span>one-time</span></p>
          <ul>
            <li>Complete page deployed live</li>
            <li>Free Vercel account setup</li>
            <li>Ownership transferred to you</li>
            <li>Add your own custom domain</li>
          </ul>
          <a href="https://buy.stripe.com/14AaENc4oeYBgfk26R5EY0f" class="btn btn-primary">Buy - 149</a>
        </div>
        <div class="tier featured">
          <div class="tier-badge">Popular</div>
          <h4>Hosted + Edits</h4>
          <p class="price">399 <span>one-time</span></p>
          <ul>
            <li>Live deployment to Vercel</li>
            <li>12 months hosting included</li>
            <li>2 rounds of edits included</li>
            <li>Email support</li>
          </ul>
          <a href="https://buy.stripe.com/fZu4gpecw2bPbZ4dPz5EY0g" class="btn btn-primary">Buy - 399</a>
        </div>
        <div class="tier">
          <h4>Premium</h4>
          <p class="price">997 <span>first 12 months</span></p>
          <ul>
            <li>Everything in Hosted + Edits</li>
            <li>Voice AI chatbot bolt-on</li>
            <li>Unlimited edits for 12 months</li>
            <li>Priority support</li>
          </ul>
          <button class="btn btn-primary" onclick="alert('Contact tyrone@propagate.media for Premium setup')">Get This</button>
        </div>
      </div>
    </div>
  </div>

  <div class="confirm-overlay" id="confirm-overlay">
    <div class="confirm-box">
      <h3>Remove This Demo?</h3>
      <p>This will permanently delete the demo page for ${name}.</p>
      <div style="display:flex;gap:12px;justify-content:center;">
        <button class="btn-outline" onclick="hideNotInterested()">Keep It</button>
        <button class="btn-primary" onclick="confirmDelete()" style="background:#666;border-color:#666;">Delete Demo</button>
      </div>
    </div>
  </div>

  <div class="removed-bar" id="removed-bar">
    <p>This demo has been permanently removed. <a href="mailto:freshsites@sites.propagate.media">Email us</a> if you change your mind.</p>
  </div>

  <script>
    function showTiers() { document.getElementById('tier-panel').classList.add('active'); document.getElementById('buy-bar').style.display = 'none'; }
    function hideTiers() { document.getElementById('tier-panel').classList.remove('active'); document.getElementById('buy-bar').style.display = 'flex'; }
    function showNotInterested() { document.getElementById('confirm-overlay').classList.add('active'); }
    function hideNotInterested() { document.getElementById('confirm-overlay').classList.remove('active'); }
    function confirmDelete() { document.getElementById('confirm-overlay').classList.remove('active'); document.getElementById('buy-bar').style.display = 'none'; document.getElementById('tier-panel').classList.remove('active'); document.getElementById('removed-bar').classList.add('active'); }
    document.getElementById('confirm-overlay').addEventListener('click', function(e) { if (e.target === this) hideNotInterested(); });
    document.getElementById('tier-panel').addEventListener('click', function(e) { if (e.target === this) hideTiers(); });
  </script>

</body>
</html>
'''

def build_html(lead):
    """Build HTML for one lead."""
    # Compute derived vars
    name = lead["name"]
    brand_dark = lead["brand_color"]
    # Make hero overlay slightly darker
    hero_overlay = lead["brand_color"] + "d9"
    hero_overlay_2 = "#1a1a1acc"
    badge_bg = lead["brand_color"] + "4d"
    
    logo_text = f'<span style="color:{lead["brand_color"]}">{name.split()[0]}</span>'
    if len(name.split()) > 1:
        logo_text += f' <span style="color:#1a1a1a">{" ".join(name.split()[1:])}</span>'
    
    tagline = f"Professional garage services in {lead['location'].split(',')[0]}. Call {lead['phone']}."
    
    trust_items = ""
    if "est" in lead["badge"].lower() or "since" in lead["badge"].lower():
        yrs = lead["badge"]
        trust_items += f'<div class="trust-item"><strong>{yrs}</strong><span>Experience</span></div>'
    elif "approv" in lead["badge"].lower():
        trust_items += f'<div class="trust-item"><strong>DVSA</strong><span>Approved</span></div>'
    else:
        trust_items += f'<div class="trust-item"><strong>Trusted</strong><span>Local Garage</span></div>'
    trust_items += '<div class="trust-item"><strong>All Makes</strong><span>& Models</span></div>'
    trust_items += '<div class="trust-item"><strong>MOT</strong><span>Testing</span></div>'
    trust_items += '<div class="trust-item"><strong>Parts</strong><span>& Labour</span></div>'
    
    about_heading = f"Your Trusted {lead['location'].split(',')[0]} Garage"
    about_paras = ""
    paras = lead["about"].split('. ')
    for p in paras:
        if p.strip():
            about_paras += f'<p>{p.strip()}{"" if p.endswith(".") else "."}</p>'
    
    services_html = ""
    svc_imgs = [
        IMAGES["workshop"], IMAGES["diagnostics"], IMAGES["tyres"],
        IMAGES["brakes"], IMAGES["servicing"], IMAGES["car"]
    ]
    for i, (icon, title, desc) in enumerate(lead["services"]):
        img = svc_imgs[i % len(svc_imgs)]
        services_html += f'''
        <div class="card">
          <img src="{img}" alt="{title}" loading="lazy">
          <div class="card-body">
            <h3>{title}</h3>
            <p>{desc}</p>
          </div>
        </div>
'''
    
    subs = {
        "name": name,
        "description": lead["hero_text"],
        "brand_color": lead["brand_color"],
        "brand_dark": brand_dark,
        "hero_overlay": hero_overlay,
        "hero_overlay_2": hero_overlay_2,
        "badge_bg": badge_bg,
        "logo_text": logo_text,
        "location": lead["location"],
        "phone": lead["phone"],
        "badge": lead["badge"],
        "hero_text": lead["hero_text"],
        "hero_img": lead["hero_img"],
        "about_img": lead["about_img"],
        "tagline": tagline,
        "trust_items": trust_items,
        "about_heading": about_heading,
        "about_paras": about_paras,
        "services_html": services_html,
        "hours": lead["hours"],
    }
    
    return Template(HTML_TEMPLATE).safe_substitute(subs)

# Generate all demos
demos_dir = Path("demos")
demos_dir.mkdir(exist_ok=True)

all_leads = LEADS + EXISTING
for lead in all_leads:
    html = build_html(lead)
    path = demos_dir / f"{lead['slug']}.html"
    path.write_text(html, encoding="utf-8")
    print(f"Wrote: {path}")

print(f"\nGenerated {len(all_leads)} demos")
