#!/usr/bin/env python3
"""
FreshSites Scoring Engine v4 - Honest Browser-Based Scoring
Uses rendered DOM + visual assessment.

Weights:
- Content: 25% (what info exists)
- Design: 40% (how it looks, mobile, modernity)
- Conversion: 35% (CTAs, phone, forms, trust)

Scores >7 = Good, 5-7 = Needs work, <5 = Needs rebuild
Target: sub-5.0 for outreach
"""
import json, re

def score_from_analysis(content_data: dict, design_data: dict, conv_data: dict) -> dict:
    """Calculate weighted score from three category analyses."""
    
    content_score = content_data["score"]
    design_score = design_data["score"] 
    conv_score = conv_data["score"]
    
    overall = round(
        (content_score * 0.25) + 
        (design_score * 0.40) + 
        (conv_score * 0.35),
        1
    )
    
    return {
        "score": overall,
        "content_score": content_score,
        "design_score": design_score,
        "conversion_score": conv_score,
        "content": content_data["findings"],
        "design": design_data["findings"],
        "conversion": conv_data["findings"],
        "raw": {
            "content": content_data["raw"],
            "design": design_data["raw"],
            "conversion": conv_data["raw"],
        }
    }

def analyze_content(snapshot: str, title: str) -> dict:
    """Analyze what content actually exists on the page."""
    text = snapshot.lower()
    findings = []
    raw = {}
    score = 5.0  # Start neutral
    
    # Services
    services = []
    service_keywords = ["servicing", "repair", "mot", "tyre", "clutch", "brake", "exhaust", "air con", "diagnostic", "timing", "wheel alignment"]
    for kw in service_keywords:
        if kw in text:
            services.append(kw.title())
    raw["services_found"] = services
    
    if len(services) >= 5:
        score += 2
        findings.append(f"Comprehensive services listed ({len(services)} found)")
    elif len(services) >= 3:
        score += 1
        findings.append(f"Core services present ({', '.join(services[:3])})")
    elif len(services) > 0:
        findings.append(f"Limited services ({', '.join(services)})")
    else:
        score -= 2
        findings.append("No visible service list")
    
    # Phone
    phone_match = re.search(r'(?:tel|phone|contact).*?(\d[\d\s\(\)\-]{8,})', snapshot, re.I)
    has_phone = phone_match is not None
    raw["phone"] = phone_match.group(1).strip() if phone_match else None
    
    if has_phone:
        score += 1.5
        findings.append(f"Phone: {raw['phone']}")
    else:
        findings.append("No phone visible")
    
    # Email  
    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', snapshot)
    has_email = email_match is not None
    raw["email"] = email_match.group(1) if email_match else None
    
    if has_email:
        score += 0.5
        findings.append(f"Email: {raw['email']}")
    
    # Hours
    has_hours = any(p in text for p in ["mon - fri", "monday", "opening times", "open:", "hours:"])
    raw["has_hours"] = has_hours
    if has_hours:
        score += 1
        findings.append("Opening hours visible")
    else:
        findings.append("No opening hours")
    
    # Location
    has_postcode = re.search(r'(?:ld|sy|hr|np|cf|sa)\d\s?\d[a-z]{2}', text) is not None
    has_town = any(t in text for t in ["llandrindod", "welshpool", "newtown", "rhayader", "montgomery", "wales"])
    raw["has_location"] = has_postcode or has_town
    
    if has_postcode:
        score += 1
        findings.append("Address with postcode")
    elif has_town:
        score += 0.5
        findings.append("Town mentioned")
    else:
        findings.append("No location visible")
    
    # About
    has_about = any(kw in text for kw in ["who we are", "about us", "independent", "established", "family run", "years experience"])
    raw["has_about"] = has_about
    if has_about:
        score += 1
        findings.append("About/identity section")
    
    score = round(max(0, min(10, score)), 1)
    return {"score": score, "findings": findings, "raw": raw}

def analyze_design(snapshot: str, title: str, url: str) -> dict:
    """Analyze design quality - visual, mobile, modernity."""
    text = snapshot.lower()
    findings = []
    raw = {}
    score = 5.0  # Start neutral
    
    # Mobile/responsive
    has_viewport = "width=device-width" in text or "viewport" in text
    raw["has_viewport"] = has_viewport
    
    if not has_viewport:
        score -= 2.5
        findings.append("NOT MOBILE-FRIENDLY - no viewport meta tag (critical)")
    else:
        findings.append("Viewport meta present")
    
    # Builder detection
    builder_sigs = {
        "wix": "Wix template",
        "squarespace": "Squarespace",
        "godaddy": "GoDaddy builder",
        "weebly": "Weebly",
        "sigmabee": "Third-party designer (Sigmabee)",
        "site by": "Third-party attribution",
        "website design": "Designer credited",
    }
    
    detected_builder = None
    for sig, label in builder_sigs.items():
        if sig in text:
            detected_builder = label
            break
    raw["builder"] = detected_builder
    
    if detected_builder:
        if "Wix" in detected_builder or "Weebly" in detected_builder:
            score -= 2
        else:
            score -= 1
        findings.append(f"Built with: {detected_builder}")
    else:
        findings.append("Custom or unknown platform")
    
    # Visual richness
    img_count = len(re.findall(r'image\s+"[^"]*"', snapshot))
    raw["image_count"] = img_count
    
    if img_count >= 5:
        score += 1
        findings.append(f"Rich imagery ({img_count} images)")
    elif img_count >= 2:
        findings.append(f"Some images ({img_count})")
    else:
        score -= 1.5
        findings.append("Very few images - looks empty")
    
    # Layout quality indicators
    section_count = len(re.findall(r'heading\s+"[^"]{3,50}"\s+\[level=([234])', snapshot))
    raw["section_count"] = section_count
    
    if section_count >= 6:
        score += 1
        findings.append("Good content structure")
    elif section_count < 3:
        score -= 1.5
        findings.append("Flat structure - no clear sections")
    
    # Age indicators
    age_issues = []
    if "table" in text and "layout" in text:
        age_issues.append("Table-based layout")
    if "<marquee" in text:
        age_issues.append("Marquee tag")
    if "visitor counter" in text:
        age_issues.append("Hit counter")
    
    raw["age_issues"] = age_issues
    if age_issues:
        score -= len(age_issues) * 1.5
        findings.append(f"Legacy elements: {', '.join(age_issues)}")
    
    # Cookie banner / popups (negative)
    has_cookie_banner = "cookie" in text and ("accept" in text or "continue" in text or "more info" in text)
    raw["cookie_banner"] = has_cookie_banner
    if has_cookie_banner:
        score -= 0.5
        findings.append("Cookie banner blocks content")
    
    # Typography/readability
    font_issues = 0
    if len(re.findall(r'font-size:\s*[0-9]{1,2}px', text)) < 3:
        font_issues += 1
    raw["font_issues"] = font_issues
    
    score = round(max(0, min(10, score)), 1)
    return {"score": score, "findings": findings, "raw": raw}

def analyze_conversion(snapshot: str, title: str) -> dict:
    """Analyze conversion elements - CTAs, forms, trust."""
    text = snapshot.lower()
    findings = []
    raw = {}
    score = 5.0
    
    # Clickable phone
    has_tel_link = 'href="tel:' in text or 'tel:' in text
    raw["has_clickable_phone"] = has_tel_link
    
    if has_tel_link:
        score += 2
        findings.append("Clickable phone link")
    else:
        phone_match = re.search(r'(?:tel|phone|contact).*?(\d[\d\s\(\)\-]{8,})', snapshot, re.I)
        if phone_match:
            score += 0.5
            findings.append("Phone visible but NOT clickable")
        else:
            findings.append("No phone number")
    
    # Forms
    has_form = "form" in text or "input" in text or "textarea" in text
    raw["has_form"] = has_form
    if has_form:
        score += 2
        findings.append("Contact form present")
    else:
        findings.append("No contact form")
    
    # CTAs
    cta_patterns = [r'book\s*now', r'call\s*now', r'get\s*quote', r'request\s*callback', r'make\s*appointment']
    cta_count = sum(1 for p in cta_patterns if re.search(p, text))
    raw["cta_count"] = cta_count
    
    if cta_count >= 2:
        score += 2
        findings.append(f"Strong CTAs ({cta_count})")
    elif cta_count == 1:
        score += 0.5
        findings.append("One CTA found")
    else:
        score -= 1
        findings.append("No clear call-to-action buttons")
    
    # Trust signals
    has_reviews = any(kw in text for kw in ["review", "testimonial", "customer said", "recommended", "google review"])
    has_social = any(kw in text for kw in ["facebook", "twitter", "instagram", "follow us"])
    has_since = any(kw in text for kw in ["since", "years experience", "established"])
    
    raw["trust_signals"] = {"reviews": has_reviews, "social": has_social, "established": has_since}
    
    trust_count = sum([has_reviews, has_social, has_since])
    if trust_count >= 2:
        score += 1.5
        findings.append("Good trust signals")
    elif trust_count == 1:
        score += 0.5
        findings.append("Minimal trust signals")
    else:
        score -= 1
        findings.append("No trust signals (reviews, social, experience)")
    
    # Map
    has_map = "map" in text or "google" in text and "directions" in text
    raw["has_map"] = has_map
    if has_map:
        score += 1
        findings.append("Map embedded")
    
    score = round(max(0, min(10, score)), 1)
    return {"score": score, "findings": findings, "raw": raw}

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 scoring_v4.py <snapshot_file> <title> <url>")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        snapshot = f.read()
    title = sys.argv[2] if len(sys.argv) > 2 else ""
    url = sys.argv[3] if len(sys.argv) > 3 else ""
    
    content = analyze_content(snapshot, title)
    design = analyze_design(snapshot, title, url)
    conv = analyze_conversion(snapshot, title)
    
    result = score_from_analysis(content, design, conv)
    print(json.dumps(result, indent=2))
