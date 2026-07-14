#!/usr/bin/env python3
"""
Reliable brand color extraction.
Prioritizes logo image analysis over CSS.
Use this when you need trustworthy brand colors.
"""
import re
import io
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
from urllib.parse import urljoin
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def fetch(url, timeout=15, binary=False):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.content if binary else r.text
    except:
        pass
    return None

def color_quality(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r, g, b = [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
        mx, mn = max(r, g, b), min(r, g, b)
        sat = 0 if mx == mn else (mx - mn) / (mx + mn) if (mx + mn) / 2 < 0.5 else (mx - mn) / (2 - mx - mn)
        lum = (mx + mn) / 2
        return {"sat": sat, "lum": lum}
    except:
        return {"sat": 0, "lum": 0.5}

def analyze_logo_image(logo_url):
    """Extract dominant saturated color from a logo image."""
    img_data = fetch(logo_url, binary=True)
    if not img_data:
        return None

    try:
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        if img.width < 16 or img.height < 16:
            return None

        # Resize for speed
        img_small = img.resize((60, 60))
        pixels = np.array(img_small).reshape(-1, 3)

        # Filter out near-white and near-black
        mask = np.all(pixels > 35, axis=1) & np.all(pixels < 245, axis=1)
        filtered = pixels[mask] if len(pixels[mask]) > 80 else pixels

        if len(filtered) < 20:
            return None

        # Cluster
        kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
        kmeans.fit(filtered)

        best_color = None
        best_score = 0

        for center in kmeans.cluster_centers_:
            r, g, b = center / 255.0
            mx, mn = max(r, g, b), min(r, g, b)
            sat = 0 if mx == mn else (mx - mn) / (mx + mn) if (mx + mn) / 2 < 0.5 else (mx - mn) / (2 - mx - mn)
            lum = (mx + mn) / 2

            # Prefer saturated, mid-luminance colors (typical brand colors)
            score = sat * (1 - abs(lum - 0.5) * 1.5)
            if score > best_score and sat > 0.18:
                best_score = score
                best_color = center.astype(int)

        if best_color is not None:
            return f"#{best_color[0]:02x}{best_color[1]:02x}{best_color[2]:02x}"
    except Exception as e:
        pass

    return None

def extract_brand_color(soup, url):
    """
    Primary method: logo image analysis.
    Fallback: saturated CSS colors.
    """
    # === 1. Try logo images first (most reliable) ===
    logo_selectors = [
        'img[alt*="logo" i]', 'img[class*="logo" i]', '#logo img', '.logo img',
        'header img', 'nav img', 'a[href*="/"] > img:first-child',
        'link[rel="apple-touch-icon"]', 'link[rel="icon"]', 'link[rel="shortcut icon"]'
    ]

    for sel in logo_selectors:
        el = soup.select_one(sel)
        if el:
            src = el.get("src") or el.get("href")
            if src:
                logo_url = urljoin(url, src)
                color = analyze_logo_image(logo_url)
                if color:
                    q = color_quality(color)
                    if q["sat"] > 0.2:
                        return color

    # === 2. Fallback to CSS (only if logo failed) ===
    style_text = ""
    for s in soup.find_all("style"):
        style_text += s.string or ""
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href", "")
        if href and not href.startswith("http"):
            css = fetch(urljoin(url, href))
            if css:
                style_text += css

    # Look for saturated brand-like colors in common selectors
    patterns = [
        r'background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,6})',
        r'--(?:primary|brand|accent|theme)-color\s*:\s*(#[0-9a-fA-F]{3,6})',
    ]

    candidates = []
    for pat in patterns:
        for m in re.finditer(pat, style_text, re.I):
            c = m.group(1)
            if len(c) == 4:
                c = f"#{c[1]*2}{c[2]*2}{c[3]*2}"
            q = color_quality(c)
            if q["sat"] > 0.25 and 0.15 < q["lum"] < 0.85:
                candidates.append((c, q["sat"]))

    if candidates:
        # Return the most saturated candidate
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    # Final fallback
    return "#c41e3a"
