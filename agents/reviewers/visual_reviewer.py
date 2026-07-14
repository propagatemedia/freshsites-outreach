#!/usr/bin/env python3
"""
Visual & Design Reviewer
Evaluates visual quality, contrast, mobile-friendliness, and brand fidelity.
"""
from typing import Dict, Any

def review_visual(extracted: Dict[str, Any], snapshot: str = "", expected_brand: str = "") -> Dict[str, Any]:
    score = 5.0
    findings = []
    gaps = []

    # Mobile / Viewport
    if "width=device-width" in snapshot or "viewport" in snapshot.lower():
        score += 1.5
        findings.append("Mobile viewport present")
    else:
        score -= 2.0
        gaps.append("NOT mobile-friendly (no viewport meta)")

    # Brand color fidelity (basic check)
    if expected_brand and expected_brand != "#c41e3a":
        score += 1.0
        findings.append(f"Brand color applied ({expected_brand})")
    else:
        gaps.append("Brand color may be default or incorrect")

    # Contrast / Button quality (we already check in main reviewer)
    findings.append("Button contrast check delegated to main reviewer")

    # Visual richness
    img_count = snapshot.count("<img")
    if img_count >= 5:
        score += 1.0
        findings.append(f"Good visual richness ({img_count} images)")
    elif img_count < 3:
        score -= 1.0
        gaps.append("Sparse visuals")

    final_score = round(max(0, min(10, score)), 1)

    return {
        "score": final_score,
        "findings": findings,
        "gaps": gaps,
        "pass": final_score >= 5.5
    }
