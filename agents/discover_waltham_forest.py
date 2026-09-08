#!/usr/bin/env python3
"""
Waltham Forest Business Discovery + Scoring via Web Search
Finds electrician, plumber, roofer, builder businesses.
Scores all, filters <5.0 with verified email.
Returns ready-to-build leads JSON.
"""

import json
import re
import sqlite3
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import subprocess

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Config ──────────────────────────────────────────────────────────
LOCATION = "Waltham Forest, London"
TRADES = {
    "electrician": 5,
    "plumber": 5,
    "roofer": 5,
    "builder": 5
}
DB_PATH = Path(__file__).parent.parent / "leads" / "freshsites.db"
OUTPUT_LEADS = Path(__file__).parent.parent / "leads" / "waltham_forest_leads.json"

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
    email_verified: bool = False

    def to_dict(self):
        return {
            "name": self.name,
            "industry": self.industry,
            "address": self.address,
            "postcode": self.postcode,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "google_maps_url": self.google_maps_url,
            "score": self.score,
            "score_breakdown": self.score_breakdown,
            "status": self.status,
            "email_verified": self.email_verified,
            "defects": self.get_defects(),
        }

    def get_defects(self):
        """Extract defects from score_breakdown."""
        if isinstance(self.score_breakdown, str):
            try:
                breakdown = json.loads(self.score_breakdown)
            except:
                return []
        else:
            breakdown = self.score_breakdown
        
        # Return penalties that are > 0
        return [k for k, v in breakdown.items() if v > 0]


# ── Database ──────────────────────────────────────────────────────
def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""
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
        );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_status ON leads(status);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_score ON leads(score);")
    conn.commit()
    conn.close()


def save_lead_to_db(lead: Lead):
    """Save or update lead in database."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"
    
    # Check if already exists
    c.execute("SELECT id FROM leads WHERE website = ? AND name = ?", (lead.website, lead.name))
    existing = c.fetchone()
    
    if existing:
        c.execute("""
            UPDATE leads SET
                score = ?, score_breakdown = ?, email = ?, phone = ?,
                status = ?, updated_at = ?, notes = ?
            WHERE id = ?
        """, (
            lead.score,
            json.dumps(lead.score_breakdown) if isinstance(lead.score_breakdown, dict) else lead.score_breakdown,
            lead.email,
            lead.phone,
            lead.status,
            now,
            lead.notes,
            existing[0]
        ))
    else:
        lead.created_at = now
        lead.updated_at = now
        c.execute("""
            INSERT INTO leads (
                name, industry, address, postcode, phone, email, website,
                google_maps_url, score, score_breakdown, status, created_at, updated_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead.name,
            lead.industry,
            lead.address,
            lead.postcode,
            lead.phone,
            lead.email,
            lead.website,
            lead.google_maps_url,
            lead.score,
            json.dumps(lead.score_breakdown) if isinstance(lead.score_breakdown, dict) else lead.score_breakdown,
            lead.status,
            now,
            now,
            lead.notes
        ))
    
    conn.commit()
    conn.close()


# ── Discovery via web_search (via Hermes tools) ──────────────────────────────────
def discover_via_web_search(trade: str, max_results: int) -> List[Dict]:
    """
    Use Hermes web_search tool to find businesses.
    This will be called from an execute_code block that has access to Hermes tools.
    For now, return stub for testing.
    """
    # This will be populated by the calling code
    return []


def extract_postcode(address: str) -> str:
    """Extract UK postcode from address."""
    if not address:
        return ""
    # UK postcode pattern: e.g., E17 9PE
    match = re.search(r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b', address, re.IGNORECASE)
    return match.group(0) if match else ""


# ── Scoring Engine ──────────────────────────────────────────────────────
def score_website(lead: Lead) -> Dict:
    """
    Score a website 0-10 based on conversion readiness.
    Uses heuristic scoring without rendering (fast path for discovery).
    """
    if not lead.website:
        return {
            "score": 9.0,
            "breakdown": {"no_website": 9.0},
            "issue": "No website found"
        }
    
    score = 5.0  # baseline
    breakdown = {}
    
    # Fetch website content
    try:
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        }
        response = requests.get(lead.website, headers=headers, timeout=5)
        content = response.text.lower()
    except Exception as e:
        return {
            "score": 8.0,
            "breakdown": {"website_unreachable": 8.0},
            "issue": f"Could not fetch: {str(e)}"
        }
    
    # Analyze content
    
    # CTA/Contact Detection
    has_contact_form = re.search(r'<form|contact|message|get.*quote|request.*quote', content, re.I) is not None
    has_phone_prominent = re.search(r'tel:|phone:|call us|0\d{3,4}\s?\d{3,4}\s?\d{3,4}', content, re.I) is not None
    has_email = re.search(r'mailto:|email|contact@', content, re.I) is not None
    
    if not has_contact_form:
        breakdown["no_contact_form"] = 1.0
        score -= 1.0
    
    if not has_phone_prominent:
        breakdown["phone_hidden"] = 1.0
        score -= 1.0
    
    if not has_email:
        breakdown["no_email_visible"] = 0.5
        score -= 0.5
    
    # Trust/Reviews
    has_reviews = re.search(r'review|testimonial|google|trustpilot|5\s*star', content, re.I) is not None
    if not has_reviews:
        breakdown["no_reviews_visible"] = 1.0
        score -= 1.0
    
    # Service clarity
    service_keywords = ["service", "repair", "installation", "maintenance", "emergency", "available"]
    service_count = sum(1 for kw in service_keywords if kw in content)
    if service_count < 2:
        breakdown["weak_service_clarity"] = 0.5
        score -= 0.5
    
    # Mobile responsiveness (heuristic)
    if 'viewport' not in content:
        breakdown["no_viewport"] = 0.5
        score -= 0.5
    
    # Design/Modernity (heuristic)
    is_builder_site = any(x in content for x in ['powered by wix', 'squarespace', 'godaddy', 'webador'])
    if is_builder_site:
        breakdown["builder_site"] = 0.5
        score -= 0.5
    
    # Trust indicators
    has_accreditation = re.search(r'accredited|certified|iso|dbs|registered', content, re.I) is not None
    if has_accreditation:
        score += 0.5
    
    # Ensure score is in range
    score = max(0.0, min(10.0, score))
    score = round(score, 1)
    
    return {
        "score": score,
        "breakdown": breakdown,
        "issue": None
    }


# ── Email Verification ──────────────────────────────────────────────────────
def verify_email_in_lead(lead: Lead) -> bool:
    """
    Check if lead has a verified public email.
    Look in: website contact page, footer, about page.
    """
    if not lead.website:
        return False
    
    if not lead.email:
        return False
    
    # Try to verify email exists on the website
    try:
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        }
        
        # Check main page
        response = requests.get(lead.website, headers=headers, timeout=5)
        content = response.text.lower()
        
        # Look for email in common locations
        email_escaped = lead.email.lower().replace("@", " at ").replace(".", " dot ")
        if lead.email.lower() in content or email_escaped in content:
            return True
        
        # Try contact page
        contact_urls = [
            lead.website.rstrip("/") + "/contact",
            lead.website.rstrip("/") + "/contact-us",
            lead.website.rstrip("/") + "/about",
        ]
        for url in contact_urls:
            try:
                resp = requests.get(url, headers=headers, timeout=5)
                if lead.email.lower() in resp.text.lower():
                    return True
            except:
                pass
        
        return False
    
    except:
        return False


# ── Main ──────────────────────────────────────────────────────────
def main():
    print(f"Discovering {LOCATION} businesses...\n")
    
    init_db()
    all_leads = []
    
    # Placeholder: web_search results will be populated by calling code
    # This script is designed to be called from execute_code with Hermes tools access
    
    print("Note: This script is designed to be called from execute_code context with Hermes web_search access.")
    print("Returning empty for now - populate from execute_code caller.\n")
    
    # Output ready-to-build leads JSON (empty for now)
    output_data = {
        "location": LOCATION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_discovered": len(all_leads),
        "qualified_leads": len(all_leads),
        "leads": [l.to_dict() for l in all_leads]
    }
    
    OUTPUT_LEADS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_LEADS, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Output saved to: {OUTPUT_LEADS}\n")
    print("Ready-to-build leads JSON:")
    print(json.dumps(output_data, indent=2))
    
    return len(all_leads)


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count > 0 else 1)
