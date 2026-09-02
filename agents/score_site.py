#!/usr/bin/env python3
"""FreshSites score_site.py - honest weak-site scoring for local trade leads.

Scores the public website a real visitor reaches. Severe defects beat vanity scores:
closed/suspended/blank/under-construction pages are rebuild targets even if they
technically return HTTP 200.

Exit 0 when the site is a valid rebuild candidate, 2 when it should be rejected,
1 on usage/internal error.
"""
from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Optional

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X) FreshSites/2.0"
SEVERE_PATTERNS = {
    "closed_site": [r"sorry this website is now closed", r"website is now closed"],
    "account_suspended": [r"account suspended", r"suspendedpage\.cgi"],
    "under_construction": [r"website under construction", r"coming soon", r"under construction"],
    "blank_lander": [r"^\s*$"],
    "domain_for_sale": [r"domain[\s\-]+(?:name[\s\-]+)?for sale", r"buy this domain", r"this domain (?:may be|is) for sale"],
    "parking_page": [r"parked free", r"sedoparking", r"this domain is parked", r"\blander\b"],
}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_parts: list[str] = []
        self.h1: list[str] = []
        self.h2h3: list[str] = []
        self.text_parts: list[str] = []
        self.forms = 0
        self.imgs = 0
        self.links = 0
        self.tel_links = 0
        self.mail_links = 0
        self.meta_viewport = False
        self.in_title = False
        self.heading: str | None = None

    def handle_starttag(self, tag, attrs):
        attrs = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self.in_title = True
        if tag in {"h1", "h2", "h3"}:
            self.heading = tag
        if tag == "form":
            self.forms += 1
        if tag == "img" and attrs.get("src"):
            self.imgs += 1
        if tag == "a":
            self.links += 1
            href = attrs.get("href", "").lower()
            self.tel_links += int(href.startswith("tel:"))
            self.mail_links += int(href.startswith("mailto:"))
        if tag == "meta" and attrs.get("name", "").lower() == "viewport":
            self.meta_viewport = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag in {"h1", "h2", "h3"}:
            self.heading = None

    def handle_data(self, data):
        s = re.sub(r"\s+", " ", data).strip()
        if not s:
            return
        self.text_parts.append(s)
        if self.in_title:
            self.title_parts.append(s)
        if self.heading == "h1" and len(self.h1) < 5:
            self.h1.append(s)
        if self.heading in {"h2", "h3"} and len(self.h2h3) < 30:
            self.h2h3.append(s)


@dataclass
class SiteScore:
    url: str
    final_url: str = ""
    http_status: int | str = ""
    score: float = 0.0
    candidate_score_100: int = 100
    decision: str = "REJECT"
    severe_defects: list[str] = field(default_factory=list)
    conversion_assets: list[str] = field(default_factory=list)
    trust_assets: list[str] = field(default_factory=list)
    service_assets: list[str] = field(default_factory=list)
    breakdown: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    title: str = ""
    h1: list[str] = field(default_factory=list)
    word_count: int = 0
    image_count: int = 0
    form_count: int = 0
    tel_links: int = 0
    mail_links: int = 0
    mobile_viewport: bool = False
    platform_signals: list[str] = field(default_factory=list)


def fetch(url: str, timeout=15) -> tuple[str, str, int | str, str | None]:
    if not re.match(r"^https?://", url):
        candidates = ["https://" + url, "http://" + url]
    else:
        candidates = [url]
    errors = []
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
    for candidate in candidates:
        try:
            req = urllib.request.Request(candidate, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                raw = r.read(800_000)
                enc = r.headers.get_content_charset() or "utf-8"
                return raw.decode(enc, "replace"), r.geturl(), r.status, None
        except urllib.error.HTTPError as e:
            try:
                body = e.read(200_000).decode("utf-8", "replace")
            except Exception:
                body = ""
            return body, e.geturl(), e.code, None
        except Exception as e:
            # A surprising number of rubbish targets have broken/self-signed SSL.
            # Retry HTTPS without verification so we can distinguish "bad cert but
            # content exists" from genuinely unreachable. The broken cert remains
            # a severe rebuild defect in the score.
            if candidate.startswith("https://") and "CERTIFICATE_VERIFY_FAILED" in str(e):
                try:
                    insecure_ctx = ssl._create_unverified_context()
                    req = urllib.request.Request(candidate, headers={"User-Agent": USER_AGENT})
                    with urllib.request.urlopen(req, timeout=timeout, context=insecure_ctx) as r:
                        raw = r.read(800_000)
                        enc = r.headers.get_content_charset() or "utf-8"
                        body = raw.decode(enc, "replace")
                        return body, r.geturl(), r.status, "ssl_certificate_invalid"
                except Exception as e2:
                    errors.append(f"{candidate}: broken SSL fallback failed: {type(e2).__name__}: {str(e2)[:120]}")
            errors.append(f"{candidate}: {type(e).__name__}: {str(e)[:120]}")
    return "", candidates[0], "FETCH_FAIL", " | ".join(errors)


def detect_platform(html: str) -> list[str]:
    low = html.lower()
    sigs = [("wixstatic", "Wix"), ("ueni", "UENI"), ("squarespace", "Squarespace"), ("weebly", "Weebly"), ("godaddy", "GoDaddy"), ("wp-content", "WordPress"), ("webflow", "Webflow")]
    return [name for sig, name in sigs if sig in low]


def score(url: str) -> SiteScore:
    html, final_url, status, err = fetch(url)
    s = SiteScore(url=url, final_url=final_url, http_status=status)
    if err:
        if err == "ssl_certificate_invalid":
            s.severe_defects.append("ssl_certificate_invalid")
            s.reasons.append("SSL certificate invalid - browser may warn/block visitors")
        else:
            s.severe_defects.append("fetch_failed")
            s.reasons.append(err)
            s.breakdown = {"site_unreachable": 1.0, "no_contact_form": 1.0, "weak_mobile": 1.0}
            s.candidate_score_100 = 0
            s.decision = "BUILD"
            return s

    parser = PageParser(); parser.feed(html[:800_000])
    text = " ".join(parser.text_parts)
    low_text = text.lower().strip()
    low_all = (html + " " + text + " " + final_url).lower()
    s.title = " ".join(parser.title_parts)[:140]
    s.h1 = parser.h1
    s.word_count = len(text.split())
    s.image_count = parser.imgs
    s.form_count = parser.forms
    s.tel_links = parser.tel_links
    s.mail_links = parser.mail_links
    s.mobile_viewport = parser.meta_viewport
    s.platform_signals = detect_platform(html)

    for defect, pats in SEVERE_PATTERNS.items():
        if any(re.search(p, low_text if defect == "blank_lander" else low_all, re.I | re.S) for p in pats):
            s.severe_defects.append(defect)
    if isinstance(status, int) and status >= 400:
        s.severe_defects.append(f"http_{status}")
    if s.word_count <= 5 and s.image_count == 0 and parser.forms == 0:
        s.severe_defects.append("blank_page")

    phone_visible = bool(re.search(r"(?:\+?44|0)\s?\d{3,5}[\s\-]?\d{3,4}[\s\-]?\d{3,4}", text)) or parser.tel_links > 0
    email_visible = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)) or parser.mail_links > 0
    cta = any(x in low_all for x in ["contact us", "get a quote", "free quote", "call now", "book", "request", "enquire", "send message"])
    map_embed = "google.com/maps" in low_all or "maps/embed" in low_all
    review_signal = any(x in low_all for x in ["review", "testimonial", "trustpilot", "rated", "5 star", "stars"])
    accreditation = any(x in low_all for x in ["niceic", "nfrc", "gas safe", "trustmark", "checkatrade", "constructionline", "fmb", "iso "])
    services = [h for h in parser.h2h3 if re.search(r"service|roof|electric|plumb|bathroom|clad|construction|repair|install|heating|boiler", h, re.I)]

    if phone_visible: s.conversion_assets.append("phone")
    if email_visible: s.conversion_assets.append("email")
    if cta: s.conversion_assets.append("cta")
    if parser.forms: s.conversion_assets.append("form")
    if map_embed: s.conversion_assets.append("map")
    if review_signal: s.trust_assets.append("reviews")
    if accreditation: s.trust_assets.append("accreditations")
    if len(services) >= 2: s.service_assets.append("service_depth")
    if s.word_count >= 400: s.service_assets.append("content_depth")

    # Start from 10 and remove visible commercial defects. Severe defects force the floor.
    score = 10.0
    b: dict[str, float] = {}
    def penalise(key, amount, reason):
        nonlocal score
        score -= amount; b[key] = max(b.get(key, 0), round(amount / 2.5, 2)); s.reasons.append(reason)

    if not parser.meta_viewport: penalise("weak_mobile", 2.0, "No mobile viewport")
    if not parser.h1: penalise("no_h1", 1.2, "No clear H1")
    if not phone_visible: penalise("phone_hidden", 1.8, "Phone not visible/clickable")
    if not cta: penalise("no_cta_above_fold", 1.4, "Weak or missing CTA")
    if not parser.forms: penalise("no_contact_form", 1.1, "No contact form")
    if not email_visible: penalise("missing_email", 0.7, "No email visible")
    if s.image_count < 2: penalise("thin_imagery", 1.0, f"Thin imagery ({s.image_count})")
    if s.word_count < 180: penalise("weak_value_prop", 1.5, f"Thin content ({s.word_count} words)")
    if not review_signal and not accreditation: penalise("social_proof", 1.0, "No trust/review/accreditation signal")
    if s.platform_signals and s.platform_signals[0] in {"UENI", "Wix", "GoDaddy"}: penalise("builder_bloat", 0.6, "Template/builder platform signal")

    if s.severe_defects:
        b.update({"severe_site_defect": 1.0, "no_contact_form": 1.0, "weak_value_prop": 1.0})
        score = min(score, 2.5 if any(d in s.severe_defects for d in ["closed_site", "account_suspended", "blank_lander", "blank_page", "fetch_failed"]) else 3.8)
        s.reasons.insert(0, "Severe defect: " + ", ".join(s.severe_defects))

    s.score = round(max(0, min(10, score)), 1)
    # Candidate matrix: lower is better for us. Severe defects hard-pass.
    s.candidate_score_100 = 0 if s.severe_defects else min(100, int((s.score * 10) + len(s.conversion_assets) * 5 + len(s.trust_assets) * 5 + len(s.service_assets) * 5))
    if s.severe_defects or s.score < 5.0:
        s.decision = "BUILD"
    elif s.score < 6.0 and len(s.conversion_assets) < 3:
        s.decision = "REVIEW"
    else:
        s.decision = "REJECT"
    s.breakdown = b or {"minor_website_gaps": 0.5}
    return s


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    result = score(args.url)
    data = asdict(result)
    if args.out:
        Path(args.out).write_text(json.dumps(data, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(f"{result.decision} {result.score}/10 {result.url} -> {result.final_url}")
        for r in result.reasons[:8]: print(f"- {r}")
    return 0 if result.decision in {"BUILD", "REVIEW"} else 2

if __name__ == "__main__":
    sys.exit(main())
