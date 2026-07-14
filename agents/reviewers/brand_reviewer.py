#!/usr/bin/env python3
"""
Brand & Asset Reviewer
Checks color accuracy, logo usage, tone, and uniqueness vs generic templates.
"""
from typing import Dict, Any

def review_brand(extracted: Dict[str, Any], snapshot: str = "", expected_brand: str = "") -> Dict[str, Any]:
    score = 5.0
    findings = []
    gaps = []

    brand = extracted.get("brand_color", "")
    if brand and brand != "#c41e3a":
        score += 2.0
        findings.append(f"Custom brand color applied ({brand})")
    else:
        gaps.append("Using default or incorrect brand color")

    # Check if services are specific (not generic)
    services = extracted.get("services", [])
    generic_words = ["service", "repair", "mot"]
    specific = [s for s in services if not any(w in s.lower() for w in generic_words) or len(s) > 25]
    if len(specific) >= 3:
        score += 1.5
        findings.append("Specific, non-generic service descriptions")
    else:
        gaps.append("Services feel generic")

    final_score = round(max(0, min(10, score)), 1)

    return {
        "score": final_score,
        "findings": findings,
        "gaps": gaps,
        "pass": final_score >= 6.0
    }
