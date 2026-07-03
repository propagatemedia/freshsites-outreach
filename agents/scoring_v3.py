#!/usr/bin/env python3
"""
FreshSites Website Scoring Matrix v3
Uses browser-rendered text content for accurate scoring.
Only scores what a real human visitor actually sees.

Usage:
    from scoring_v3 import score_website_v3, WEAKNESS_MAP
"""

import re
from typing import Optional


WEAKNESS_MAP = {
    "no_h1": "No clear headline saying what you do",
    "weak_value_prop": "Value proposition is vague or buried",
    "no_cta_above_fold": "No clear action button above the fold",
    "phone_hidden": "Phone number hard to find",
    "no_opening_hours": "Opening hours not visible",
    "generic_title": "Page title is weak in Google search results",
    "builder_bloat": "Slow builder site that hurts loading speed",
    "no_contact_form": "No contact form for enquiries",
    "weak_mobile": "Mobile experience needs improvement",
}


def score_website_v3(rendered_text: str, title: str, url: str, has_iframes: bool = False) -> tuple[float, dict]:
    """
    Score a local business website 0-10 based on RENDERED content.
    
    rendered_text: The visible text content (from browser innerText)
    title: Browser page title
    url: Website URL
    has_iframes: Whether the page uses iframes (builder signal)
    """
    text = rendered_text.lower()
    breakdown = {}
    
    # === 1. First Impression ===
    
    # H1 / headline quality
    # Check if there's a strong headline early in the text
    first_500 = rendered_text[:500].lower()
    h1_signals = ["mot", "repair", "service", "garage", "vehicle", "car"]
    h1_matches = sum(1 for s in h1_signals if s in first_500)
    # Also check title
    title_has_keywords = any(s in title.lower() for s in h1_signals)
    breakdown["no_h1"] = 0 if (h1_matches >= 2 and len(title) > 15 and title_has_keywords) else 1
    
    # Value prop
    vp_signals = ["since", "year", "experience", "trusted", "local", "family", "reliable", "quality"]
    vp_matches = sum(1 for s in vp_signals if s in first_500)
    breakdown["weak_value_prop"] = 0 if vp_matches >= 2 else 1
    
    # === 2. Conversion ===
    
    # CTA quality
    cta_signals = ["book", "call", "enquire", "contact", "quote", "appointment", "schedule", "now"]
    cta_matches = sum(1 for s in cta_signals if s in text)
    has_strong_cta = any(s in text for s in ["book now", "call now", "get a quote", "schedule"])
    breakdown["no_cta_above_fold"] = 0 if (has_strong_cta or cta_matches >= 3) else 1
    
    # Phone visibility
    phone = re.search(r"\b0\d{3,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b", rendered_text)
    phone_in_first_1000 = re.search(r"\b0\d{3,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b", rendered_text[:1000])
    breakdown["phone_hidden"] = 0 if phone_in_first_1000 else (0.5 if phone else 1)
    
    # Opening hours
    hours_signals = ["monday", "tuesday", "opening", "hours", "open", "closed", "am", "pm", "8:", "9:", "weekday"]
    hours_matches = sum(1 for s in hours_signals if s in text)
    breakdown["no_opening_hours"] = 0 if hours_matches >= 3 else 1
    
    # Contact form
    form_signals = ["name", "email", "message", "submit", "send", "form", "enquiry"]
    form_matches = sum(1 for s in form_signals if s in text)
    breakdown["no_contact_form"] = 0 if form_matches >= 4 else 1
    
    # === 3. Trust ===
    
    # Social proof / reviews
    review_signals = ["review", "testimonial", "what customers", "what people", "rating", "star", "google review", "facebook"]
    review_matches = sum(1 for s in review_signals if s in text)
    breakdown["social_proof"] = 0 if review_matches >= 1 else 1
    
    # Personal touch
    personal_signals = ["colin", "owner", "manager", "team", "since", "experience", "family"]
    personal_matches = sum(1 for s in personal_signals if s in text)
    breakdown["no_personal_touch"] = 0 if personal_matches >= 2 else 1
    
    # Location
    postcode = re.search(r"[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}", rendered_text)
    breakdown["no_location"] = 0 if postcode else 1
    
    # === 4. Technical ===
    
    # Title quality
    title_score = 0
    if not title or len(title) < 10:
        title_score = 1
    elif title.lower() in ["home", "index", "homepage"]:
        title_score = 1
    elif len(title) < 20:
        title_score = 0.5
    else:
        title_score = 0
    breakdown["generic_title"] = title_score
    
    # Builder bloat signal
    builder_signals = ["wix", "squarespace", "godaddy", "weebly", "strikingly"]
    raw_url_lower = url.lower()
    has_builder = any(s in raw_url_lower for s in builder_signals) or has_iframes
    breakdown["builder_bloat"] = 1 if has_builder else 0
    
    # Mobile (viewport check done separately, assume ok if viewport present)
    # We flag mobile issues only if we can't verify
    breakdown["weak_mobile"] = 0  # Will be set externally based on viewport check
    
    # === CALCULATE ===
    weights = {
        "no_h1": 1.0,
        "weak_value_prop": 0.8,
        "no_cta_above_fold": 1.0,
        "phone_hidden": 0.8,
        "no_opening_hours": 0.5,
        "generic_title": 0.6,
        "builder_bloat": 0.8,
        "no_contact_form": 0.7,
        "weak_mobile": 0.8,
    }
    
    raw_score = sum(breakdown.get(k, 0) * weights[k] for k in weights)
    max_penalty = sum(weights.values())
    score = round(10 - ((raw_score / max_penalty) * 10), 1)
    
    return max(0, min(10, score)), breakdown


def get_weaknesses_v3(breakdown: dict) -> list[str]:
    """Return human-readable weakness descriptions."""
    result = []
    for key, value in breakdown.items():
        if value > 0.3:
            result.append(WEAKNESS_MAP.get(key, key.replace("_", " ").title()))
    return result


# Backward compat
score_website = score_website_v3
get_weaknesses = get_weaknesses_v3
