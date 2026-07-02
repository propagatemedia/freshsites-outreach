#!/usr/bin/env python3
"""
FreshSites Website Scoring Matrix v2
Scores websites 0-10 on conversion-critical dimensions.
Focus: What actually hurts a local business website from making money.

Usage:
    from scoring import score_website, WEAKNESS_MAP
"""

from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse


# What each metric means and why it matters
WEAKNESS_MAP = {
    "speed_signal": "Page loads slowly — visitors leave before seeing your content",
    "mobile_ux": "Broken or awkward mobile experience — 60%+ of visitors are on phones",
    "no_cta_above_fold": "No clear action button in the first screen — visitors don't know what to do",
    "phone_hidden": "Phone number buried or missing — callers can't find you",
    "no_contact_form_above_fold": "No enquiry form above the fold — losing leads who won't scroll",
    "no_social_proof": "No reviews, testimonials, or trust signals — visitors don't believe you're real",
    "generic_title": "Page title is weak or missing — Google shows junk in search results",
    "no_h1": "No main headline — visitors can't tell what you do in 3 seconds",
    "weak_value_prop": "No clear value proposition — visitors bounce to competitors",
    "no_location_signal": "No address or local signals — Google and visitors don't know where you are",
    "broken_elements": "Broken links or errors — looks unmaintained and unprofessional",
    "builder_bloat": "Built on slow website builder — kills SEO ranking and page speed",
    "no_opening_hours": "No opening hours visible — customers don't know when to call or visit",
    "no_services_list": "No clear services shown — visitors don't know if you do what they need",
    "no_personal_touch": "No owner name, team photos, or story — looks like a faceless business",
}


def score_website_v2(soup: BeautifulSoup, url: str, load_time_ms: float = 0) -> tuple[float, dict]:
    """
    Score a local business website 0-10.
    
    Higher score = better at converting visitors into customers.
    7+ = good enough. < 7 = losing money.
    """
    text = soup.get_text(separator=" ", strip=True)
    domain = urlparse(url).netloc.lower()
    
    breakdown = {}
    
    # === DIMENSION 1: First Impression (can they tell what you do in 3 seconds?) ===
    
    # 1.1: Has clear H1
    h1 = soup.find("h1")
    h1_text = h1.get_text(strip=True) if h1 else ""
    h1_words = len(h1_text.split()) if h1_text else 0
    breakdown["no_h1"] = 0 if (h1 and h1_words >= 2) else 1
    
    # 1.2: Value proposition visible (not just "Home" or company name)
    hero_text = ""
    hero_candidates = soup.select(".hero, section:first-of-type, .banner, [class*='hero'], [class*='banner']")
    if hero_candidates:
        hero_text = hero_candidates[0].get_text(strip=True)
    if not hero_text:
        # Try first 500 chars of body
        hero_text = text[:500]
    
    value_signals = [
        "garage", "mot", "repair", "service", "mechanic", "tyre",
        "since", "year", "experience", "local", "family", "trusted",
        "book", "call", "today", "now", "free", "quote"
    ]
    value_matches = sum(1 for s in value_signals if s in hero_text.lower())
    breakdown["weak_value_prop"] = 0 if value_matches >= 3 else 1
    
    # === DIMENSION 2: Trust (why should they believe you?) ===
    
    # 2.1: Social proof
    review_patterns = [
        r"\b(review|testimonial|feedback|rating|star|google review)\b",
        r"\b(what (our|people) say|customer review)\b",
    ]
    has_reviews = any(re.search(p, text, re.I) for p in review_patterns)
    breakdown["no_social_proof"] = 0 if has_reviews else 1
    
    # 2.2: Personal touch (owner name, team, story)
    personal_signals = ["owner", "manager", "team", "since", "year", "experience", "family", "founder"]
    personal_matches = sum(1 for s in personal_signals if s in text.lower())
    breakdown["no_personal_touch"] = 0 if personal_matches >= 2 else 1
    
    # 2.3: Location visible
    # Look for postcode pattern
    postcode = re.search(r"[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}", text)
    address_words = ["street", "road", "drive", "lane", "avenue", "close", "industrial estate"]
    has_address = any(w in text.lower() for w in address_words)
    breakdown["no_location_signal"] = 0 if (postcode or has_address) else 1
    
    # === DIMENSION 3: Conversion (can they easily become a customer?) ===
    
    # 3.1: CTA above fold
    cta_words = re.compile(r"\b(book|call|contact|enquir|quote|appointment|schedule|get in|reserve|find out)\b", re.I)
    cta_count = len(soup.find_all(string=cta_words))
    breakdown["no_cta_above_fold"] = 0 if cta_count >= 2 else 1
    
    # 3.2: Phone visible
    phone = re.search(r"\b0\d{3,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b", text)
    breakdown["phone_hidden"] = 0 if phone else 1
    
    # 3.3: Contact form present (not just email)
    forms = soup.find_all("form")
    has_real_form = any(
        any(f.get("type") in ["text", "email", "tel"] for f in form.find_all("input"))
        for form in forms
    )
    breakdown["no_contact_form_above_fold"] = 0 if has_real_form else 1
    
    # 3.4: Opening hours
    hours_signals = ["monday", "tuesday", "opening", "hours", "open", "closed", "am", "pm"]
    hours_matches = sum(1 for s in hours_signals if s in text.lower())
    breakdown["no_opening_hours"] = 0 if hours_matches >= 3 else 1
    
    # === DIMENSION 4: SEO & Discoverability (can Google find you?) ===
    
    # 4.1: Title quality
    title = soup.title.string.strip() if soup.title else ""
    title_score = 0
    if not title or len(title) < 10:
        title_score = 1  # Missing or very short
    elif title.lower() in ["home", "index", "homepage", "untitled"]:
        title_score = 1  # Generic
    elif len(title.split("|")) >= 2 and any(w in title.lower() for w in ["garage", "mot", "repair", "service"]):
        title_score = 0  # Good: has separators and keywords
    elif len(title) > 50:
        title_score = 0  # Descriptive
    else:
        title_score = 0.5  # OK but could be better
    breakdown["generic_title"] = title_score
    
    # 4.2: Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    has_desc = meta_desc and len(meta_desc.get("content", "")) > 30
    # Also check Open Graph
    og_desc = soup.find("meta", property="og:description") or soup.find("meta", property="og:title")
    breakdown["generic_title"] = max(breakdown["generic_title"], 0 if (has_desc or og_desc) else 1)
    
    # 4.3: Services visible
    service_signals = ["mot", "service", "repair", "tyre", "diagnostic", "clutch", "brake", "exhaust"]
    service_matches = sum(1 for s in service_signals if s in text.lower())
    breakdown["no_services_list"] = 0 if service_matches >= 3 else 1
    
    # === DIMENSION 5: Technical Quality ===
    
    # 5.1: Builder bloat signal
    builder_signals = ["wix.com", "squarespace", "godaddy", "weebly", " strikingly", "export_website"]
    raw_html = str(soup)[:2000]
    has_builder = any(s in raw_html.lower() or s in url.lower() for s in builder_signals)
    breakdown["builder_bloat"] = 1 if has_builder else 0
    
    # 5.2: Speed estimate
    # Count resources
    scripts = len(soup.find_all("script"))
    styles = len(soup.find_all("link", rel="stylesheet"))
    images = len(soup.find_all("img"))
    estimated_bloat = scripts + styles * 0.5 + images * 0.2
    breakdown["speed_signal"] = 1 if estimated_bloat > 25 else (0.5 if estimated_bloat > 15 else 0)
    
    # 5.3: Mobile viewport
    viewport = soup.find("meta", attrs={"name": "viewport"})
    breakdown["mobile_ux"] = 0 if viewport else 1
    
    # 5.4: Broken links (404s we can detect from fragments)
    broken_patterns = ["#", "javascript:void", "tel:", "mailto:"]
    nav_links = [a.get("href", "") for a in soup.find_all("a", href=True)]
    empty_links = sum(1 for h in nav_links if h in ["#", "", "/"] or "javascript:void" in h)
    total_links = len(nav_links) or 1
    breakdown["broken_elements"] = 1 if (empty_links / total_links) > 0.3 else 0
    
    # === CALCULATE SCORE ===
    weights = {
        # First impression (critical)
        "no_h1": 0.8,
        "weak_value_prop": 1.0,
        # Trust
        "no_social_proof": 0.8,
        "no_personal_touch": 0.5,
        "no_location_signal": 0.6,
        # Conversion
        "no_cta_above_fold": 1.0,
        "phone_hidden": 0.8,
        "no_contact_form_above_fold": 0.7,
        "no_opening_hours": 0.6,
        # SEO
        "generic_title": 0.6,
        "no_services_list": 0.7,
        # Technical
        "builder_bloat": 0.7,
        "speed_signal": 0.8,
        "mobile_ux": 0.8,
        "broken_elements": 0.5,
    }
    
    raw_score = sum(breakdown[k] * weights[k] for k in weights)
    max_penalty = sum(weights.values())
    
    # Invert: 0 penalty = 10, full penalty = 0
    score = round(10 - ((raw_score / max_penalty) * 10), 1)
    
    return score, breakdown


def get_weaknesses(breakdown: dict) -> list[str]:
    """Return human-readable weakness descriptions."""
    result = []
    for key, value in breakdown.items():
        if value > 0.3:  # Significant penalty
            result.append(WEAKNESS_MAP.get(key, key))
    return result


# Backward compat
score_website = score_website_v2
