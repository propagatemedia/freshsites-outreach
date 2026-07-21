#!/usr/bin/env python3
import json, sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'leads' / 'freshsites.db'
EXTRACTED = ROOT / 'extracted'
EXTRACTED.mkdir(exist_ok=True)

leads = [
    {
        'name': 'Ricky Mobile Mechanic & Diagnostics Ltd',
        'slug': 'ricky-mobile-mechanic-diagnostics',
        'website': 'https://ricky-mobilemechanic-diagnostics.co.uk/',
        'email': 'rickymobilemechanicdiagnostics@gmail.com',
        'phone': '07377059254',
        'address': 'West End Works, West End, Bangor LL57 2UU',
        'score': 2.3,
        'breakdown': {'weak_value_prop': 0.8, 'no_clear_cta': 0.8, 'dated_design': 1.0, 'cluttered_announcements': 0.7, 'weak_trust_above_fold': 0.4},
        'notes': 'Vision-qualified ROOT homepage 2026-07-21: loud red/yellow amateur layout, announcement clutter, no clear conversion hierarchy. Public email from homepage extract.',
        'services': ['Emergency callouts and breakdowns', 'Diagnostics', 'Servicing', 'Clutches and brakes', 'Suspension', 'MOT failure work', 'Tyres', 'DPF regeneration', 'Air conditioning regas'],
        'about': 'Mobile mechanic and diagnostics business based in North Wales with over 28 years experience, offering callouts, diagnostics, servicing, repairs, tyres and MOT failure work.',
        'hours': 'Monday - Friday: 8:30 - 17:30 | Saturday: 8:30 - 12:00',
        'brand_color': '#d71920',
        'location': 'Bangor, LL57 2UU'
    },
    {
        'name': 'Crossing Garage',
        'slug': 'crossing-garage',
        'website': 'https://crossing-garage.co.uk/',
        'email': 'contact@crossing-garage.co.uk',
        'phone': '01597 829243',
        'address': 'Tremont Road, Llandrindod Wells, LD1 5BH',
        'score': 3.5,
        'breakdown': {'dated_design': 0.9, 'weak_hero': 0.8, 'weak_cta': 0.7, 'thin_trust': 0.5, 'old_wordpress_layout': 0.6},
        'notes': 'Vision-qualified ROOT homepage 2026-07-21: old WordPress-style layout, weak hero/CTA, no strong modern trust layer. Email verified from indexed site/privacy page.',
        'services': ['MOT testing', 'Car servicing', 'Car repairs', 'Light commercial vehicle repairs', 'Diagnostics', 'Brakes', 'Clutches'],
        'about': 'Independent garage based in Llandrindod Wells offering a full range of services for car and light commercial vehicle owners throughout mid Wales.',
        'hours': 'Monday - Friday: 8:30 - 17:30 | Saturday: 9:00 - 12:00',
        'brand_color': '#1f4f8f',
        'location': 'Llandrindod Wells, LD1 5BH'
    },
    {
        'name': 'K.F. Autos Waterlooville',
        'slug': 'kf-autos-waterlooville',
        'website': 'http://kfautoswaterlooville.co.uk/',
        'email': 'karlfaircloughautos@gmail.com',
        'phone': '07766731599 / 023 9229 9625',
        'address': 'Waterlooville',
        'score': 3.7,
        'breakdown': {'weak_conversion': 0.7, 'no_reviews_above_fold': 0.5, 'broken_whitespace': 0.8, 'template_design': 0.7, 'thin_trust': 0.4},
        'notes': 'Vision-qualified ROOT homepage 2026-07-21: generic hero, service cards but huge broken whitespace/dead lower page, no strong trust/review layer above fold.',
        'services': ['Car repairs', 'MOTs', 'Servicing', 'Car tyres', 'Brakes', 'Exhausts', 'Clutches', 'Engine diagnostics', 'DPF cleaning'],
        'about': 'Local Waterlooville garage offering vehicle repairs, MOTs, servicing, tyres, brakes, exhausts, clutches, diagnostics and DPF cleaning.',
        'hours': 'Monday - Friday: 8:00 - 17:00',
        'brand_color': '#00388f',
        'location': 'Waterlooville'
    },
    {
        'name': 'Ron Hill Motors',
        'slug': 'ron-hill-motors',
        'website': 'https://www.ronhillmotors.co.uk/',
        'email': 'ronhillmotors@hotmail.com',
        'phone': '0151 486 6118',
        'address': 'Unit 6-7, Woodend Industrial Estate, Woodend Avenue, Speke, Liverpool, L24 9NB',
        'score': 3.2,
        'breakdown': {'dated_design': 1.0, 'weak_hierarchy': 0.8, 'third_party_form_branding': 0.5, 'weak_services_presentation': 0.6, 'thin_trust': 0.4},
        'notes': 'Vision-qualified ROOT homepage 2026-07-21: pasted flyer look, harsh red section, cheap third-party form, weak service presentation, limited trust.',
        'services': ['MOT testing', 'General mechanic services', 'Servicing', 'Oil and filter changes', 'Cambelts', 'Motorbike MOTs'],
        'about': 'Family-based general mechanic and MOT test centre for cars and motorbikes in Speke, Liverpool, established in 1970.',
        'hours': 'Monday - Friday: 8:30 - 17:30 | Saturday: 8:30 - 12:00',
        'brand_color': '#e90743',
        'location': 'Speke, Liverpool, L24 9NB'
    },
    {
        'name': 'B D Motors Ltd',
        'slug': 'bd-motors-ltd',
        'website': 'https://www.bdmotorsltd.co.uk/',
        'email': 'danielbrian53@gmail.com',
        'phone': '01404 851 043 / 07827 614 139',
        'address': 'Talaton, Exeter',
        'score': 3.6,
        'breakdown': {'intrusive_popup': 0.7, 'dated_design': 0.8, 'broken_map': 0.6, 'broken_bullets': 0.5, 'weak_trust_layer': 0.5},
        'notes': 'Vision-qualified ROOT homepage 2026-07-21: intrusive red popup, dated Yell-style layout, broken bullet indentation, blank map, weak visible review/trust layer.',
        'services': ['Car servicing', 'Car repairs', 'Car diagnostics', 'MOT preparation', 'Breakdown recovery', 'Roadside assistance', 'Wheel alignment'],
        'about': 'Car garage serving Talaton, Exeter and Honiton with over 40 years experience, offering servicing, repairs, diagnostics, MOT preparation and recovery.',
        'hours': 'Monday - Friday: 8:30 - 17:30 | Saturday: 8:30 - 12:00',
        'brand_color': '#e42a18',
        'location': 'Talaton, Exeter'
    },
]

now = datetime.now().isoformat()
conn = sqlite3.connect(DB)
cur = conn.cursor()
for lead in leads:
    slug = lead['slug']
    demo_url = f'https://propagatemedia.github.io/freshsites-outreach/demos/{slug}.html'
    extracted = {
        'name': lead['name'],
        'slug': slug,
        'url': lead['website'],
        'title': lead['name'],
        'brand_color': lead['brand_color'],
        'services': lead['services'],
        'about': lead['about'],
        'hours': lead['hours'],
        'phone': lead['phone'],
        'email': lead['email'],
        'location': lead['location'],
        'images': [],
        'extracted_at': now,
    }
    (EXTRACTED / f'{slug}.json').write_text(json.dumps(extracted, indent=2), encoding='utf-8')
    cur.execute('DELETE FROM leads WHERE name = ? AND website = ?', (lead['name'], lead['website']))
    cur.execute('''
        INSERT INTO leads (name, industry, address, phone, email, website, score, score_breakdown, demo_url, status, created_at, updated_at, notes)
        VALUES (?, 'garage', ?, ?, ?, ?, ?, ?, ?, 'demo_built', ?, ?, ?)
    ''', (lead['name'], lead['address'], lead['phone'], lead['email'], lead['website'], lead['score'], json.dumps(lead['breakdown']), demo_url, now, now, lead['notes']))
    print(f"prepared {slug}: {lead['name']} -> {demo_url}")
conn.commit()
conn.close()
print(f"Prepared {len(leads)} verified leads")
