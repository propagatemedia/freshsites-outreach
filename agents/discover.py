#!/usr/bin/env python3
"""
FreshSites Discovery + Scoring Agent
Finds automotive businesses in target area, audits their websites,
scores them 0-10, flags < 7 for outreach.

Usage:
    PYTHONPATH="" ./.venv/bin/python3 agents/discover.py
"""

import json
import re
import sqlite3
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

# ── Config ──────────────────────────────────────────────────────────
TARGET_AREA = "Powys, Wales"
SEARCH_QUERIES = [
    "garage Newtown Powys Wales",
    "MOT centre Welshpool Powys Wales",
    "car repair Brecon Powys Wales",
    "tyre fitting Llandrindod Wells Powys",
    "auto repair Machynlleth Powys Wales",
    "garage services Montgomery Powys Wales",
]
MIN_SCORE = 7.0
DB_PATH = Path(__file__).parent.parent / "leads" / "freshsites.db"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


# ── Data Model ──────────────────────────────────────────────────────
@dataclass
class Lead:
    name: str = ""
    industry: str = ""
    address: str = ""
    postcode: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    google_maps_url: str = ""
    score: float = 0.0
    score_breakdown: dict = field(default_factory=dict)
    screenshot_path: str = ""
    demo_url: str = ""
    status: str = "new"
    created_at: str = ""
    updated_at: str = ""
    notes: str = ""


# ── Database ──────────────────────────────────────────────────────
def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            industry TEXT,
            address TEXT,
            postcode TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            google_maps_url TEXT,
            score REAL DEFAULT 0,
            score_breakdown TEXT,
            screenshot_path TEXT,
            demo_url TEXT,
            status TEXT DEFAULT 'new',
            created_at TEXT,
            updated_at TEXT,
            notes TEXT
        )
        """
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_status ON leads(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_score ON leads(score)")
    conn.commit()
    conn.close()


def upsert_lead(lead: Lead) -> int:
    lead.updated_at = datetime.utcnow().isoformat()
    if not lead.created_at:
        lead.created_at = lead.updated_at
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    # Check by domain
    domain = urlparse(lead.website).netloc.lower().replace("www.", "") if lead.website else ""
    if domain:
        c.execute("SELECT id FROM leads WHERE website LIKE ?", (f"%{domain}%",))
        row = c.fetchone()
    else:
        c.execute("SELECT id FROM leads WHERE name=? AND postcode=?", (lead.name, lead.postcode))
        row = c.fetchone()

    data = {
        **asdict(lead),
        "score_breakdown": json.dumps(lead.score_breakdown),
    }
    if row:
        lead_id = row[0]
        c.execute(
            """
            UPDATE leads SET
                industry=:industry, address=:address, postcode=:postcode,
                phone=:phone, email=:email, website=:website,
                google_maps_url=:google_maps_url, score=:score,
                score_breakdown=:score_breakdown, screenshot_path=:screenshot_path,
                demo_url=:demo_url, status=:status, updated_at=:updated_at,
                notes=:notes
            WHERE id=:id
            """,
            {**data, "id": lead_id},
        )
    else:
        c.execute(
            """
            INSERT INTO leads (name, industry, address, postcode, phone, email,
                website, google_maps_url, score, score_breakdown, screenshot_path,
                demo_url, status, created_at, updated_at, notes)
            VALUES (:name, :industry, :address, :postcode, :phone, :email,
                :website, :google_maps_url, :score, :score_breakdown, :screenshot_path,
                :demo_url, :status, :created_at, :updated_at, :notes)
            """,
            data,
        )
        lead_id = c.lastrowid
    conn.commit()
    conn.close()
    return lead_id


def get_lead_by_domain(domain: str) -> Optional[dict]:
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT * FROM leads WHERE website LIKE ?", (f"%{domain}%",))
    row = c.fetchone()
    conn.close()
    if row:
        cols = [d[0] for d in c.description]
        return dict(zip(cols, row))
    return None


# ── Website Fetch + Score ──────────────────────────────────────────

def fetch_website(url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
    try:
        if not url.startswith("http"):
            url = "https://" + url
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"    Fetch failed: {e}")
        return None


def score_website(soup: BeautifulSoup, url: str) -> tuple[float, dict]:
    """Score 0-10 across conversion-critical metrics."""
    text = soup.get_text(separator=" ", strip=True)
    breakdown = {}

    # 1. Mobile responsive (viewport meta)
    viewport = soup.find("meta", attrs={"name": "viewport"})
    breakdown["mobile_responsive"] = 1 if viewport else 0

    # 2. Clear CTA (book/call/contact/quote action)
    cta_words = re.compile(
        r"\b(book|call|contact|quote|enquire|appointment|schedule|get in|free|reserve)\b",
        re.I,
    )
    cta_count = len(soup.find_all(string=cta_words))
    breakdown["cta_present"] = min(2, cta_count)  # 0, 1, or 2

    # 3. Phone number visible
    phone_pattern = re.compile(r"\b0\d{3,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b")
    breakdown["phone_visible"] = 1 if phone_pattern.search(text) else 0

    # 4. Social proof (testimonials/reviews/stars)
    social_words = re.compile(
        r"\b(testimonial|review|what our|customer say|feedback|star|rating|google review|trustpilot)\b",
        re.I,
    )
    breakdown["social_proof"] = 1 if soup.find(string=social_words) else 0

    # 5. Page title quality
    title = soup.title.string.strip() if soup.title else ""
    breakdown["title_quality"] = (
        2 if len(title) > 30 and title.lower() not in ["home", "index"]
        else 1 if len(title) > 10
        else 0
    )

    # 6. Has H1 with real text
    h1 = soup.find("h1")
    h1_text = h1.get_text(strip=True) if h1 else ""
    breakdown["h1_present"] = (
        2 if len(h1_text) > 20
        else 1 if len(h1_text) > 5
        else 0
    )

    # 7. Contact form
    forms = soup.find_all("form")
    breakdown["contact_form"] = 1 if forms else 0

    # 8. Social links
    social_domains = ["facebook.com", "twitter.com", "x.com", "instagram.com", "linkedin.com"]
    social_links = sum(
        1 for a in soup.find_all("a", href=True)
        if any(sd in a["href"] for sd in social_domains)
    )
    breakdown["social_links"] = min(1, social_links)

    # 9. Image count (content richness)
    imgs = soup.find_all("img")
    breakdown["images"] = min(2, len(imgs) // 3)

    # 10. SEO basics (meta description)
    meta_desc = soup.find("meta", attrs={"name": "description"})
    breakdown["meta_description"] = 1 if meta_desc and meta_desc.get("content", "") else 0

    # 11. Clean URL structure (no query strings in nav)
    nav_links = [a.get("href", "") for a in soup.find_all("a", href=True)]
    messy_urls = sum(1 for h in nav_links if "?" in h or "&" in h)
    breakdown["clean_urls"] = 0 if messy_urls > 5 else 1

    # Weighted scoring — normalize to 0-10
    weights = {
        "mobile_responsive": 1.0,
        "cta_present": 1.5,
        "phone_visible": 0.5,
        "social_proof": 1.0,
        "title_quality": 0.5,
        "h1_present": 1.0,
        "contact_form": 1.0,
        "social_links": 0.5,
        "images": 0.5,
        "meta_description": 0.5,
        "clean_urls": 0.5,
    }
    max_values = {
        "mobile_responsive": 1,
        "cta_present": 2,
        "phone_visible": 1,
        "social_proof": 1,
        "title_quality": 2,
        "h1_present": 2,
        "contact_form": 1,
        "social_links": 1,
        "images": 2,
        "meta_description": 1,
        "clean_urls": 1,
    }
    weighted = sum(breakdown[k] * weights[k] for k in weights)
    max_possible = sum(max_values[k] * weights[k] for k in weights)
    score = round((weighted / max_possible) * 10, 1)

    return score, breakdown


def extract_business_info(result: dict) -> Optional[Lead]:
    """Extract structured info from a web search result."""
    title = result.get("title", "").split("|")[0].split("-")[0].strip()
    url = result.get("url", "")
    snippet = result.get("description", "")

    if not url or not url.startswith("http"):
        return None

    # Skip directory/listing sites
    skip_domains = [
        "honestjohn.co.uk", "good-garage-guide", "infoisinfo",
        "cargarages.co.uk", "national.co.uk", "honda.co.uk",
        "mot-testers.co.uk", "motcheck.org.uk", "yell.com",
        "google.com/maps", "facebook.com", "checkatrade.com",
    ]
    if any(sd in url for sd in skip_domains):
        return None

    # Extract postcode from snippet
    postcode_match = re.search(r"[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}", snippet)
    postcode = postcode_match.group(0) if postcode_match else ""

    # Extract phone
    phone_match = re.search(r"\b0\d{3,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b", snippet)
    phone = phone_match.group(0) if phone_match else ""

    # Extract email
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", snippet)
    email = email_match.group(0) if email_match else ""

    lead = Lead(
        name=title,
        website=url,
        postcode=postcode,
        phone=phone,
        email=email,
        google_maps_url=url,
        notes=snippet[:200],
    )
    return lead


# ── Main Pipeline ───────────────────────────────────────────────────

def discover_and_score_seed_data():
    """Score the real Powys businesses from manual research."""
    seed_businesses = [
        {"name": "Grooms Garage Ltd", "website": "https://www.groomsgarage.co.uk/", "postcode": "SY16 1DL", "phone": "01686 626731"},
        {"name": "DC Auto Repairs Ltd", "website": "https://dcautorepairs.co.uk/", "postcode": "SY16", "phone": "01686 624445"},
        {"name": "K's Garage", "website": "https://ksgaragenewtown.co.uk/", "postcode": "SY16 4BQ", "phone": "01686 941274"},
        {"name": "Bradleys Garage", "website": "https://bradleysgarage.co.uk/", "postcode": "SY18 6RB", "phone": ""},
        {"name": "Newtown Tyres Ltd", "website": "https://newtowntyres.co.uk/", "postcode": "SY16 4LE", "phone": "01686 624862"},
        {"name": "BTS The Garage Adfa", "website": "https://www.btstyres.co.uk/", "postcode": "SY16 3DB", "phone": "01938 811199"},
        {"name": "Dolwen Garage Limited", "website": "", "postcode": "SY16 4HX", "phone": ""},
        {"name": "Border Garage Welshpool", "website": "https://www.motwelshpool.co.uk/", "postcode": "SY21 8RP", "phone": "01938 554444"},
        {"name": "Welshpool Autofit", "website": "https://welshpoolautofit.co.uk/", "postcode": "SY21", "phone": ""},
        {"name": "Blakemore's Autos", "website": "https://blakemoresautos.co.uk/", "postcode": "SY21 7AZ", "phone": ""},
        {"name": "William Nunns", "website": "http://www.williamnunns.co.uk/", "postcode": "SY21", "phone": ""},
        {"name": "Jacks Tyres Limited", "website": "https://www.welshpooltyres.co.uk/", "postcode": "SY21 7AZ", "phone": "01938 553554"},
        {"name": "Car and Van Welshpool", "website": "https://carandvanwelshpool.co.uk/", "postcode": "SY21", "phone": ""},
        {"name": "Al's Autos Brecon", "website": "https://alsautosbrecon.co.uk/", "postcode": "LD3 8BL", "phone": "01874 624318"},
        {"name": "J&P Engineering", "website": "", "postcode": "LD3 9AH", "phone": "01874 624397"},
        {"name": "Ian Jones Tyres Brecon", "website": "https://ianjonestyres.co.uk/", "postcode": "LD3", "phone": "01874 622905"},
        {"name": "Brecon Ford", "website": "", "postcode": "LD3 8BT", "phone": "01874 622401"},
        {"name": "Brecon Motors", "website": "https://breconmotors.co.uk/", "postcode": "LD3", "phone": "01874 611721"},
        {"name": "Brecon Car Sales", "website": "", "postcode": "LD3 8DL", "phone": "01874 623311"},
    ]

    init_db()
    all_leads = []
    qualified = []

    print(f"{'='*60}")
    print(f"FreshSites Discovery — {TARGET_AREA}")
    print(f"{'='*60}\n")

    for biz in seed_businesses:
        name = biz["name"]
        url = biz["website"]
        print(f"🔍 {name}")

        if not url:
            print(f"   └─ SKIP: No website")
            continue

        # Fetch + score
        soup = fetch_website(url)
        if not soup:
            print(f"   └─ SKIP: Website unreachable")
            continue

        score, breakdown = score_website(soup, url)

        lead = Lead(
            name=name,
            industry="garage",
            website=url,
            postcode=biz.get("postcode", ""),
            phone=biz.get("phone", ""),
            score=score,
            score_breakdown=breakdown,
        )
        lead_id = upsert_lead(lead)
        all_leads.append(lead)

        status_emoji = "🚨" if score < MIN_SCORE else "✅"
        print(f"   ├─ Score: {score}/10 {status_emoji}")

        if score < MIN_SCORE:
            qualified.append(lead)
            print(f"   ├─ QUALIFIED for outreach")
            # Show weaknesses
            weak = [k for k, v in breakdown.items() if v == 0]
            if weak:
                print(f"   └─ Weaknesses: {', '.join(weak[:3])}")
            else:
                print(f"   └─ Below threshold but no zero scores")
        else:
            print(f"   └─ Good enough")

        time.sleep(1)

    # Summary
    print(f"\n{'='*60}")
    print(f"RESULTS: {len(all_leads)} scored, {len(qualified)} qualified (< {MIN_SCORE})")
    print(f"{'='*60}\n")

    if qualified:
        print("🎯 PRIORITY OUTREACH LIST:")
        for l in qualified:
            weak = [k for k, v in l.score_breakdown.items() if v == 0]
            print(f"  • {l.name} — {l.score}/10 → {l.website}")
            if weak:
                print(f"    Weak: {', '.join(weak[:4])}")

    return qualified


if __name__ == "__main__":
    discover_and_score_seed_data()
