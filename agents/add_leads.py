#!/usr/bin/env python3
import sqlite3, json
conn = sqlite3.connect('leads/freshsites.db')
c = conn.cursor()

new_leads = [
    ('Bradleys Garage', 'info@bradleysgarage.co.uk', 'https://bradleysgarage.co.uk/', 2.7, {"no_h1":1,"no_cta_above_fold":1,"phone_hidden":0.7,"no_contact_form":0.6,"no_opening_hours":0.4}),
    ('D A Autos', 'info@daautoswelshpool.co.uk', 'https://daautoswelshpool.co.uk/', 2.3, {"no_h1":1,"no_cta_above_fold":1,"phone_hidden":0.7,"weak_value_prop":0.6,"no_contact_form":0.4}),
    ('DC Autos Newtown', 'info@dcautorepairs.co.uk', 'https://dcautorepairs.co.uk/', 2.3, {"no_h1":1,"weak_value_prop":0.8,"no_cta_above_fold":0.6,"phone_hidden":0.5,"no_opening_hours":0.4}),
    ("K's Garage", 'info@ksgaragenewtown.co.uk', 'https://ksgaragenewtown.co.uk/', 2.7, {"no_h1":1,"no_cta_above_fold":1,"phone_hidden":0.7,"weak_value_prop":0.6,"no_contact_form":0.4}),
    ('Border Garage', 'info@bordergarage.co.uk', 'https://www.motwelshpool.co.uk/', 3.2, {"no_h1":1,"no_cta_above_fold":0.8,"phone_hidden":0.5,"no_contact_form":0.4,"weak_value_prop":0.4}),
    ('Evans Motors', 'info@evansmotorsgarage.co.uk', 'https://evansmotorsgarage.co.uk/', 3.1, {"no_h1":1,"no_cta_above_fold":1,"phone_hidden":0.6,"no_contact_form":0.5,"weak_value_prop":0.3}),
    ('J T Hughes Newtown', 'info@jthughesnewtown.co.uk', 'https://jthughesnewtown.co.uk/', 3.0, {"no_h1":1,"no_cta_above_fold":0.8,"phone_hidden":0.5,"no_contact_form":0.4,"weak_value_prop":0.4}),
]

for lead in new_leads:
    name, email, website, score, breakdown = lead
    slug = name.lower().replace("'", '').replace(' ', '-')
    demo_url = f'https://propagatemedia.github.io/freshsites-outreach/demos/{slug}.html'
    c.execute('INSERT OR REPLACE INTO leads (name, email, website, score, score_breakdown, demo_url, status) VALUES (?,?,?,?,?,?,?)',
              (name, email, website, score, json.dumps(breakdown), demo_url, 'demo_built'))
    print(f'Added: {name} ({score}/10) - {slug}.html')

conn.commit()
conn.close()
print()
print('Done. 7 new leads added.')
