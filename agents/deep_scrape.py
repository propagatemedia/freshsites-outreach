#!/usr/bin/env python3
"""
Deep Site Scraper v2
Uses browser hydration to extract ALL content from a target site.
Scrapes every page, extracts services, contact, schema, reviews, about, hours.
Outputs a rich JSON file for the demo generator.

Usage: python3 agents/deep_scrape.py <url>
"""
import json, re, time, sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

EXTRACTED_DIR = Path(__file__).parent.parent / "extracted"
EXTRACTED_DIR.mkdir(exist_ok=True)

# Service keywords for garage sites
SERVICE_KEYWORDS = [
    "mot", "servicing", "service", "repair", "repairs", "tyre", "tyres", "exhaust",
    "clutch", "brake", "brakes", "diagnostic", "diagnostics", "air con", "air conditioning",
    "timing belt", "wheel alignment", "collection", "delivery", "recovery",
    "battery", "alternator", "starter", "suspension", "shock absorber", "abs",
    "dpf", "catalytic", "exhaust", "welding", "mot test", "pre-mot",
    "fleet", "commercial vehicle", "van", "4x4", "motorcycle", "moped",
    "puncture", "tracking", "geometry", "camshaft", "turbo", "remap", "tuning"
]

CONTACT_KEYWORDS = [
    "phone", "tel", "telephone", "call", "mobile", "fax",
    "email", "e-mail", "mail", "enquiries",
    "address", "location", "find us", "where",
    "hours", "opening", "open", "mon", "tue", "wed", "thu", "fri", "sat", "sun",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]

ABOUT_KEYWORDS = [
    "about", "who we are", "welcome", "established", "family run", "independent",
    "years experience", "since", "our story", "background", "history"
]

TRUST_KEYWORDS = [
    "review", "reviews", "testimonial", "testimonials", "recommend",
    "customer", "feedback", "google review", "rated", "stars",
    "approved", "accredited", "certified", "member", "partner",
    "rac", "aa", "rite", "trading standards", "which"
]


def scrape_site(url: str) -> dict:
    """Deep scrape a site using browser navigation."""
    # We need to use the browser tools directly
    # This function is called from execute_code where browser tools are available
    pass


def parse_snapshot(snapshot_text: str) -> dict:
    """Parse a browser accessibility snapshot into structured data."""
    text = snapshot_text
    low = text.lower()

    # Extract phone numbers (UK format)
    phones = re.findall(r'(?:tel:)?(\d{4,5}\s?\d{3}\s?\d{3,4}|\d{5}\s?\d{6})', text)
    phones = list(set(phones))[:3]

    # Extract emails
    emails = re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
    emails = list(set(emails))[:3]

    # Extract postcode (UK)
    postcodes = re.findall(r'([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})', text)
    postcodes = list(set(postcodes))[:2]

    # Extract headings (service names)
    headings = re.findall(r'heading\s+"([^"]{3,80})"\s+\[level=([234])', text)
    services = []
    for h, level in headings:
        h_lower = h.lower()
        if any(kw in h_lower for kw in SERVICE_KEYWORDS) and h not in services:
            services.append(h)

    # Extract all text content for about/contact detection
    static_texts = re.findall(r'StaticText\s+"([^"]{10,300})"', text)
    all_text = " ".join(static_texts)

    # About section
    about = ""
    for kw in ABOUT_KEYWORDS:
        if kw in low:
            # Get nearby text
            idx = low.find(kw)
            about = all_text[max(0, idx-100):idx+300].strip()
            break

    # Hours
    hours = ""
    for kw in ["mon", "monday", "opening", "hours"]:
        if kw in low:
            idx = low.find(kw)
            hours = all_text[max(0, idx):idx+200].strip()
            break

    # Trust signals
    trust_found = []
    for kw in TRUST_KEYWORDS:
        if kw in low:
            trust_found.append(kw)

    # Location/address
    location = ""
    if postcodes:
        location = postcodes[0]
    for kw in ["address", "location", "find us", "where"]:
        if kw in low:
            idx = low.find(kw)
            location = all_text[max(0, idx):idx+200].strip()
            break

    return {
        "phones": phones,
        "emails": emails,
        "postcodes": postcodes,
        "services": services[:10],
        "about": about[:500],
        "hours": hours[:300],
        "trust_signals": trust_found,
        "location": location[:300],
        "all_text": all_text[:5000],
    }


def merge_with_browser_data(scraped: dict, browser_snapshot: str, url: str, title: str) -> dict:
    """Merge parsed snapshot data with browser metadata."""
    parsed = parse_snapshot(browser_snapshot)

    # Create slug
    slug = re.sub(r'\W+', '-', url.replace('https://', '').replace('http://', '').rstrip('/'))
    slug = re.sub(r'^-+|-+$', '', slug)

    # Pick best phone
    phone = ""
    if parsed["phones"]:
        phone = parsed["phones"][0]
    # Also check for tel: links
    tel_match = re.search(r'href="tel:([\d\s\(\)\-+]+)"', browser_snapshot)
    if tel_match:
        phone = tel_match.group(1).strip()

    # Pick best email
    email = parsed["emails"][0] if parsed["emails"] else ""

    # Pick best location
    location = parsed["location"] if parsed["location"] else ""
    if parsed["postcodes"] and not location:
        location = parsed["postcodes"][0]

    # Pick best hours
    hours = parsed["hours"] if parsed["hours"] else ""

    return {
        "name": title.split("|")[0].strip() if "|" in title else title.split("—")[0].strip(),
        "slug": slug,
        "url": url,
        "title": title,
        "phone": phone,
        "email": email,
        "location": location,
        "hours": hours,
        "services": parsed["services"],
        "about": parsed["about"],
        "trust_signals": parsed["trust_signals"],
        "brand_color": "#D32F2F",  # Will be overridden by brand color extractor
        "raw_text": parsed["all_text"][:3000],
        "scraped_at": datetime.now().isoformat(),
    }
