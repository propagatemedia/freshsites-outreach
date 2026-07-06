#!/usr/bin/env python3
"""
Stripe Product + Payment Link Setup
Creates 3 FreshSites products and generates payment links.

Usage:
    PYTHONPATH="" ./.venv/bin/python3.11 agents/stripe_setup.py
"""

import os
import sys
from pathlib import Path

# Load .env
def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

load_env()

import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe.api_key:
    print("ERROR: STRIPE_SECRET_KEY not found in .env")
    sys.exit(1)

print(f"Stripe mode: {os.getenv('STRIPE_MODE', 'unknown')}")
print(f"Key prefix: {stripe.api_key[:15]}...")

# Product definitions
PRODUCTS = [
    {
        "name": "FreshSites - Buy Outright",
        "description": "Complete HTML page file. Host anywhere. Edit anything. No recurring fees.",
        "price_pence": 14900,
        "html_placeholder": "PLACEHOLDER_OUTRIGHT",
    },
    {
        "name": "FreshSites - Hosted + Edits",
        "description": "Hosted 2 years + 2 edit rounds included. SSL + priority email support.",
        "price_pence": 39900,
        "html_placeholder": "PLACEHOLDER_HOSTED",
    },
    {
        "name": "FreshSites - Premium",
        "description": "12 months unlimited edits + Voice AI bolt-on + full support.",
        "price_pence": 99700,
        "html_placeholder": "PLACEHOLDER_PREMIUM",
    },
]


def create_or_get_product(name: str, description: str):
    """Create Stripe product or return existing."""
    # Search for existing product by name
    existing = stripe.Product.search(query=f'name~"{name}"', limit=1)
    if existing.data:
        print(f"  Found existing product: {existing.data[0].id}")
        return existing.data[0]

    product = stripe.Product.create(
        name=name,
        description=description,
        metadata={"source": "freshsites-automation"},
    )
    print(f"  Created product: {product.id}")
    return product


def create_price(product_id: str, price_pence: int):
    """Create a price for the product."""
    price = stripe.Price.create(
        product=product_id,
        unit_amount=price_pence,
        currency="gbp",
    )
    print(f"  Created price: {price.id} - £{price_pence/100:.0f}")
    return price


def create_payment_link(price_id: str, product_name: str):
    """Create a payment link for the price."""
    # Search for existing link via list
    links = stripe.PaymentLink.list(limit=100)
    for link in links.data:
        # Check if this link uses our price by fetching line items
        try:
            items = stripe.PaymentLink.list_line_items(link.id, limit=1)
            if items.data and items.data[0].price.id == price_id:
                print(f"  Found existing link: {link.url}")
                return link
        except Exception:
            continue

    link = stripe.PaymentLink.create(
        line_items=[{"price": price_id, "quantity": 1}],
        after_completion={"type": "redirect", "redirect": {"url": "https://propagatemedia.github.io/freshsites-outreach/thanks.html"}},
        metadata={"product": product_name, "source": "freshsites"},
    )
    print(f"  Created link: {link.url}")
    return link


def update_html_links(replacements: dict):
    """Replace placeholder links in HTML files with real ones."""
    demo_dir = Path(__file__).parent.parent / "demos"
    docs_dir = Path(__file__).parent.parent / "docs" / "demos"

    updated = 0
    for html_path in list(demo_dir.glob("*.html")) + list(docs_dir.glob("*.html")):
        content = html_path.read_text()
        original = content
        for placeholder, real_url in replacements.items():
            content = content.replace(f"https://buy.stripe.com/{placeholder}", real_url)
        if content != original:
            html_path.write_text(content)
            updated += 1
            print(f"  Updated: {html_path.name}")

    return updated


def main():
    print("=" * 60)
    print("FreshSites Stripe Setup")
    print("=" * 60)

    # Verify Stripe connection
    try:
        # Test with a lightweight call instead of account read
        products = stripe.Product.list(limit=1)
        print("Stripe connected successfully")
    except Exception as e:
        print(f"ERROR: Cannot connect to Stripe: {e}")
        sys.exit(1)

    replacements = {}

    for product_def in PRODUCTS:
        print(f"\n{product_def['name']} (£{product_def['price_pence']/100:.0f})")
        print("-" * 40)

        # Create/get product
        product = create_or_get_product(product_def["name"], product_def["description"])

        # Create price
        price = create_price(product.id, product_def["price_pence"])

        # Create payment link
        link = create_payment_link(price.id, product_def["name"])

        # Store for HTML update
        replacements[product_def["html_placeholder"]] = link.url

    # Update HTML files
    print(f"\n{'=' * 60}")
    print("Updating HTML files...")
    updated = update_html_links(replacements)
    print(f"Updated {updated} HTML files")

    # Print summary
    print(f"\n{'=' * 60}")
    print("PAYMENT LINKS")
    print("=" * 60)
    for name, url in replacements.items():
        print(f"{name}: {url}")

    print("\nDone. Commit and push to deploy.")


if __name__ == "__main__":
    main()
