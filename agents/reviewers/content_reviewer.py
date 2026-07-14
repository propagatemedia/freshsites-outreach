#!/usr/bin/env python3
"""
Content Reviewer
Evaluates depth and quality of business information on the site.
"""
from typing import Dict, List, Any

def review_content(extracted: Dict[str, Any], snapshot: str = "") -> Dict[str, Any]:
    """
    Returns structured content quality assessment.
    """
    score = 5.0
    findings = []
    gaps = []

    # Services
    services = extracted.get("services", [])
    if len(services) >= 6:
        score += 2.0
        findings.append(f"Strong service depth ({len(services)} services)")
    elif len(services) >= 4:
        score += 1.0
        findings.append(f"Good service coverage ({len(services)})")
    else:
        gaps.append("Limited services listed")

    # Contact depth
    has_phone = bool(extracted.get("phone"))
    has_email = bool(extracted.get("email"))
    has_address = bool(extracted.get("location"))
    has_hours = bool(extracted.get("hours"))

    contact_score = sum([has_phone, has_email, has_address, has_hours])
    if contact_score >= 3:
        score += 1.5
        findings.append("Strong contact information")
    else:
        gaps.append(f"Weak contact depth ({contact_score}/4)")

    # About / Trust
    about = extracted.get("about", "")
    if len(about) > 200:
        score += 1.5
        findings.append("Good about/trust content")
    elif len(about) > 80:
        score += 0.5
    else:
        gaps.append("Weak or missing about section")

    # Schema / Structured data hints (future)
    # For now we just note if we see rich content

    final_score = round(max(0, min(10, score)), 1)

    return {
        "score": final_score,
        "findings": findings,
        "gaps": gaps,
        "pass": final_score >= 6.0
    }
