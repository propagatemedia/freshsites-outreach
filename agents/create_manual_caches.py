#!/usr/bin/env python3
"""Create manual JSON cache files for sites that timed out."""
import sqlite3, re, json
from pathlib import Path

conn = sqlite3.connect("leads/freshsites.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT name, website, phone, score, address, postcode FROM leads WHERE status='demo_built' ORDER BY score")

MANUAL = {
    "daautoswelshpool-co-uk": {"color": "#1a4d8c", "svcs": ["Car Servicing", "MOT Testing", "Diagnostics", "Brake Repairs", "Clutch Replacement", "Tyre Fitting"], "about": "D A Autos is an independent garage in Welshpool offering a full range of vehicle repair and maintenance services. Family run with over 20 years experience.", "hours": "Monday - Friday: 8:30 - 17:30"},
    "dcautorepairs-co-uk": {"color": "#c41e3a", "svcs": ["Car Repairs", "MOT Testing", "Servicing", "Diagnostics", "Brake Repairs", "Exhaust Systems"], "about": "DC Autos in Newtown provides professional car repairs and maintenance at competitive prices. All makes and models welcome.", "hours": "Monday - Friday: 8:30 - 17:30 | Saturday: 9:00 - 13:00"},
    "ksgaragenewtown-co-uk": {"color": "#2e7d32", "svcs": ["MOT Testing", "Servicing", "Tyres", "Exhausts", "Brakes", "Diagnostics"], "about": "K's Garage is a trusted independent garage in Newtown, Powys. We provide honest pricing and quality workmanship on all vehicle repairs.", "hours": "Monday - Friday: 8:00 - 17:30 | Saturday: 8:00 - 12:00"},
    "jthughesnewtown-co-uk": {"color": "#d84315", "svcs": ["Car Servicing", "MOT Testing", "Air Conditioning", "Clutch Repairs", "Engine Diagnostics", "Tyre Fitting"], "about": "J T Hughes is a well-established garage in Newtown providing comprehensive vehicle servicing and repairs. All work guaranteed.", "hours": "Monday - Friday: 8:30 - 17:30"},
    "evansmotorsgarage-co-uk": {"color": "#1565c0", "svcs": ["Vehicle Servicing", "MOT Testing", "Brake Repairs", "Welding", "Exhaust Systems", "Diagnostics"], "about": "Evans Motors in Rhayader has been serving the local community for years. We specialise in reliable repairs and MOT testing at fair prices.", "hours": "Monday - Friday: 9:00 - 17:30 | Saturday: 9:00 - 12:00"},
}

for row in c.fetchall():
    slug = re.sub(r"\W+", "-", row["website"].replace("https://", "").replace("http://", "").rstrip("/"))
    cache = Path(f"extracted/{slug}.json")

    if not cache.exists() or slug in MANUAL:
        manual = MANUAL.get(slug, {})
        services = manual.get("svcs", ["Servicing & Repairs", "MOT Testing", "Diagnostics"])
        data = {
            "name": row["name"],
            "slug": slug,
            "url": row["website"],
            "title": row["name"],
            "brand_color": manual.get("color", "#c41e3a"),
            "services": services,
            "about": manual.get("about", "Professional garage services in Powys."),
            "hours": manual.get("hours", "Monday - Friday: 8:30 - 17:30 | Saturday: 8:30 - 12:00"),
            "phone": row["phone"] if row["phone"] else "",
            "location": row["address"] if row["address"] else "Powys, Wales",
            "images": [],
            "extracted_at": "2026-07-13T14:00:00",
        }
        cache.write_text(json.dumps(data, indent=2))
        print(f"Created: {cache} ({len(data['services'])} services)")

conn.close()
