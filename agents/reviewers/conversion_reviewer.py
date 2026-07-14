#!/usr/bin/env python3
"""
Conversion Reviewer
Evaluates CTA strength, form quality, phone visibility, and value proposition.
"""
from typing import Dict, Any

def review_conversion(extracted: Dict[str, Any], snapshot: str = "") -> Dict[str, Any]:
    score = 5.0
    findings = []
    gaps = []

    has_phone = bool(extracted.get("phone"))
    has_form = "form" in snapshot.lower() or extracted.get("email")

    if has_phone:
        score += 1.5
        findings.append("Phone number present")
    else:
        gaps.append("No phone number visible")

    if has_form:
        score += 2.0
        findings.append("Contact form present")
    else:
        gaps.append("No contact form")

    # CTA strength (basic)
    cta_count = snapshot.lower().count("book") + snapshot.lower().count("call now") + snapshot.lower().count("get in touch")
    if cta_count >= 2:
        score += 1.5
        findings.append("Strong CTA presence")
    else:
        gaps.append("Weak calls to action")

    final_score = round(max(0, min(10, score)), 1)

    return {
        "score": final_score,
        "findings": findings,
        "gaps": gaps,
        "pass": final_score >= 6.0
    }
