#!/usr/bin/env python3
"""
Extract structured data from target garage websites. Saves to JSON cache.
Uses both CSS analysis and logo pixel extraction for brand colors.
Retries with exponential backoff on timeout.
"""

import sys, re, json, urllib.parse, time, os
from pathlib import Path
from datetime import datetime
import numpy as np
import requests
from bs4 import BeautifulSoup
from PIL import Image

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.5",
}

CACHE_DIR = Path(__file__).parent.parent / "extracted"
CACHE_DIR.mkdir(exist_ok=True)
MAX_RETRIES = 3
RETRY_DELAY = 5


def fetch(url, retries=MAX_RETRIES, binary=False):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                if attempt < retries - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return r.content if binary else r.text
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
    return None


def color_quality(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    mx, mn = max(r, g, b), min(r, g, b)
    sat = 0 if mx == mn else (mx - mn) / (mx + mn) if (mx + mn) / 2 < 0.5 else (mx - mn) / (2 - mx - mn)
    return {"sat": sat, "lum": (mx + mn) / 2}


def extract_brand_color(soup, url):
    """Try CSS, then meta tags, then logo pixel extraction."""
    style_text = ""
    for s in soup.find_all("style"):
        style_text += s.string or ""
    # Fetch linked stylesheets
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href", "")
        if href and not href.startswith("http"):
            css = fetch(urllib.parse.urljoin(url, href))
            if css:
                style_text += css

    # Inline styles
    for tag in soup.select("nav, header, .navbar, .header, .brand, .btn, div[class*='bg-']"):
        style_text += " " + tag.get("style", "")

    # Color patterns
    patterns = [
        r'[#.]btn(?:-primary)?\s*\{[^}]*background(?:-color)?:\s*(#[0-9a-fA-F]{3,6})',
        r'(?::\s*|--)(?:primary|brand|theme)-color\s*:\s*(#[0-9a-fA-F]{3,6})',
        r'[#.]nav(?:bar)?\s*\{[^}]*background(?:-color)?:\s*(#[0-9a-fA-F]{3,6})',
        r'[#.]header\s*\{[^}]*background(?:-color)?:\s*(#[0-9a-fA-F]{3,6})',
        r'.logo\s*\{[^}]*(?:background-)?(?:color)?:\s*(#[0-9a-fA-F]{3,6})',
        r'[#.]footer\s*\{[^}]*background(?:-color)?:\s*(#[0-9a-fA-F]{3,6})',
    ]

    for pat in patterns:
        ms = re.findall(pat, style_text, re.IGNORECASE)
        for m in ms:
            color = m
            if len(color) == 4:
                color = f"#{color[1] * 2}{color[2] * 2}{color[3] * 2}"
            q = color_quality(color)
            if q["sat"] > 0.15 and q["lum"] < 0.85:
                return color

    # Meta theme-color
    theme = soup.find("meta", {"name": "theme-color"}) or soup.find("meta", {"name": "msapplication-TileColor"})
    if theme:
        c = theme.get("content", "")
        if re.match(r"^#[0-9a-fA-F]{3,6}$", c):
            q = color_quality(c)
            if q["sat"] > 0.15:
                return c

    # Logo/favicon pixel extraction
    logo_url = None
    for sel in ['link[rel="shortcut icon"]', 'link[rel="icon"]', 'link[rel="apple-touch-icon"]',
                'img[class*="logo"]', '.logo img']:
        el = soup.select_one(sel)
        if el and (el.get("href") or el.get("src")):
            logo_url = urllib.parse.urljoin(url, el.get("href") or el.get("src"))
            break

    if logo_url:
        img_data = fetch(logo_url, binary=True)
        if img_data:
            try:
                import io
                img = Image.open(io.BytesIO(img_data)).convert("RGB")
                if img.width >= 16 and img.height >= 16:
                    img_small = img.resize((50, 50))
                    pixels = np.array(img_small).reshape(-1, 3)
                    mask = np.all(pixels > 40, axis=1) & np.all(pixels < 240, axis=1)
                    filtered = pixels[mask] if len(pixels[mask]) > 100 else pixels
                    from sklearn.cluster import KMeans
                    kmeans = KMeans(n_clusters=5, random_state=0, n_init=10)
                    kmeans.fit(filtered)
                    best_color, best_sat = None, 0
                    for center in kmeans.cluster_centers_:
                        r, g, b = center / 255.0
                        mx, mn = max(r, g, b), min(r, g, b)
                        sat = 0 if mx == mn else (mx - mn) / mx
                        if sat > best_sat:
                            best_sat = sat
                            best_color = center.astype(int)
                    if best_color is not None and best_sat > 0.2:
                        return f"#{best_color[0]:02x}{best_color[1]:02x}{best_color[2]:02x}"
            except Exception:
                pass

    return "#c41e3a"


def extract_services(soup):
    svc_keywords = ["servic", "MOT", "repair", "tyre", "exhaust", "brake", "clutch",
                    "batter", "diagnostic", "air con", "air-con", "timing belt",
                    "remap", "tuning", "collection", "recovery", "welding",
                    "gearbox", "suspension", "wheel", "filter", "pads", "discs",
                    "DPF", "flywheel", "turbo", "alternator", "balancing"]

    services = []
    for sel in ["#our-services", "#services", "[id*='service']", ".services"]:
        sec = soup.select_one(sel)
        if sec:
            for tag in sec.find_all(["h2", "h3", "h4", "li", "span"]):
                txt = re.sub(r'^[\s\-–—]+', '', tag.get_text(strip=True))
                if 3 < len(txt) < 80 and any(kw.lower() in txt.lower() for kw in svc_keywords):
                    if "lorem" not in txt.lower() and txt not in services:
                        services.append(txt)
            if services:
                break

    if not services:
        for heading in soup.find_all(["h2", "h3", "h4", "li"]):
            txt = heading.get_text(strip=True)
            if 3 < len(txt) < 80 and any(kw.lower() in txt.lower() for kw in svc_keywords):
                if txt not in services:
                    services.append(txt)
    return services[:10]


def extract_about(soup):
    for h in soup.find_all(["h2", "h3"]):
        txt = h.get_text(strip=True).lower()
        if any(kw in txt for kw in ["about", "welcome", "who we are"]):
            paras = []
            sibling = h.find_next_sibling()
            while sibling and sum(len(p) for p in paras) < 400:
                if sibling.name == "p":
                    paras.append(sibling.get_text(strip=True))
                sibling = sibling.find_next_sibling()
            if paras:
                return " ".join(paras)
    # Fallback
    best = ""
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if len(text) > len(best) and 20 < len(text) < 600:
            if any(s in text.lower() for s in ["since", "year", "family", "established", "experience", "local", "serving"]):
                best = text
    return best if best else "Local garage providing professional vehicle services."


def extract_hours(soup):
    html = str(soup)
    patterns = [
        r'(?:Mon-?Fri|Monday[^,]*(?:to|-)[^,]*(?:Sat|Sunday|5|6|17|18))[^<]{10,60}',
        r'(?:Open(?:ing)?\s*Hours?|Business\s*Hours)[^:]*:[^<]{10,80}',
    ]
    for p in patterns:
        m = re.search(p, html, re.I)
        if m:
            clean = re.sub(r'<[^>]+>', '', m.group(0)).strip()
            clean = re.sub(r'\s+', ' ', clean)
            if len(clean) > 10:
                return clean
    return "Monday - Friday: 8:30 - 17:30 | Saturday: 8:30 - 12:00"


def extract_phone(soup):
    text = soup.get_text()
    m = re.search(r'(?:Tel|Telephone|Phone|Call)[:\s]*\s*(0\d{3,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4})', text, re.I)
    if m:
        return m.group(1)
    m = re.search(r'\b(0\d{3,4}[\s\-]\d{3,4}[\s\-]\d{3,4})\b', text)
    if m:
        return m.group(1)
    return ""


def extract_location(text):
    m = re.search(r'([A-Z][a-z]+(?:[\s,]+[A-Z][a-z]+){0,3}),?\s+([A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2})', text)
    if m:
        return f"{m.group(1)}, {m.group(2)}"
    return "Powys, Wales"


def extract_images(soup, url):
    imgs = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or any(skip in src.lower() for skip in ["icon-sm", "blank", "spacer", "pixel"]):
            continue
        full = urllib.parse.urljoin(url, src)
        return imgs[:5]


def analyze_site(url):
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    name = re.sub(r'\s*\|.*|\s*-.*', '', title).strip()

    return {
        "name": name,
        "slug": re.sub(r'\W+', '-', url.replace("https://", "").replace("http://", "").rstrip("/")),
        "url": url,
        "title": title,
        "brand_color": extract_brand_color(soup, url),
        "services": extract_services(soup),
        "about": extract_about(soup),
        "hours": extract_hours(soup),
        "phone": extract_phone(soup),
        "location": extract_location(text),
        "images": extract_images(soup, url),
        "extracted_at": datetime.now().isoformat(),
    }


def save_cache(data, slug=None):
    slug = slug or data.get("slug")
    path = CACHE_DIR / f"{slug}.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"  Saved: {path}")
    return path


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <url> [slug]")
        sys.exit(1)
    url = sys.argv[1]
    slug = sys.argv[2] if len(sys.argv) > 2 else None

    data = analyze_site(url)
    if data:
        save_cache(data, slug)
        print(json.dumps(data, indent=2))  # Only JSON to stdout
    else:
        print(json.dumps({"error": "Failed to fetch"}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
