#!/usr/bin/env python3
"""
Stripe Webhook Handler + Purchase Delivery
Receives Stripe checkout events, stores purchases, triggers delivery.

Usage:
    # Run as webhook server
    PYTHONPATH="" ./.venv/bin/python3.11 agents/webhook_handler.py --server

    # Process a checkout manually
    PYTHONPATH="" ./.venv/bin/python3.11 agents/webhook_handler.py --session cs_test_xxx
"""

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, str(Path(__file__).parent))

DB_PATH = Path(__file__).parent.parent / "leads" / "freshsites.db"
HIMALAYA_BIN = Path.home() / ".local" / "bin" / "himalaya"
SUPPORT_EMAIL = "tyrone@propagate.media"

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")


# Tier config
TIERS = {
    "14900": {"name": "Buy Outright", "delivery": "zip_email", "hours": 2},
    "39900": {"name": "Hosted + Edits", "delivery": "deploy", "hours": 24},
    "99700": {"name": "Premium", "delivery": "full_service", "hours": 24},
}


def init_purchases_table():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stripe_session_id TEXT UNIQUE,
            stripe_payment_intent TEXT,
            customer_email TEXT,
            customer_name TEXT,
            amount_pence INTEGER,
            tier_name TEXT,
            delivery_method TEXT,
            business_name TEXT,
            status TEXT DEFAULT 'paid',
            created_at TEXT,
            delivered_at TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()


def store_purchase(session: dict) -> dict:
    """Store purchase in database."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    amount = session.get("amount_total", 0)
    tier = TIERS.get(str(amount), {"name": "Unknown", "delivery": "manual", "hours": 48})

    # Extract customer info
    customer_email = ""
    customer_name = ""
    if session.get("customer_details"):
        customer_email = session["customer_details"].get("email", "")
        customer_name = session["customer_details"].get("name", "")

    purchase = {
        "stripe_session_id": session["id"],
        "stripe_payment_intent": session.get("payment_intent", ""),
        "customer_email": customer_email,
        "customer_name": customer_name,
        "amount_pence": amount,
        "tier_name": tier["name"],
        "delivery_method": tier["delivery"],
        "business_name": "Welshpool Autofit",  # TODO: derive from session metadata
        "status": "paid",
        "created_at": datetime.utcnow().isoformat(),
        "notes": json.dumps({"checkout_url": session.get("url", "")}),
    }

    try:
        c.execute("""
            INSERT INTO purchases (stripe_session_id, stripe_payment_intent, customer_email,
                customer_name, amount_pence, tier_name, delivery_method, business_name,
                status, created_at, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, tuple(purchase.values()))
        conn.commit()
        print(f"  Stored purchase: {purchase['stripe_session_id']}")
    except sqlite3.IntegrityError:
        print(f"  Already recorded: {purchase['stripe_session_id']}")

    conn.close()
    return purchase


def send_notification(purchase: dict):
    """Send email notification about new purchase."""
    if not HIMALAYA_BIN.exists():
        print(f"  Himalaya not found, skipping notification")
        return

    subject = f"New Sale: {purchase['tier_name']} - {purchase['business_name']}"
    body = f"""New FreshSites purchase:

Tier: {purchase['tier_name']}
Amount: {purchase['amount_pence']/100:.0f}
Customer: {purchase['customer_name']} <{purchase['customer_email']}>
Business: {purchase['business_name']}
Delivery: {purchase['delivery_method']} (within {TIERS.get(str(purchase['amount_pence']), {}).get('hours', 48)} hours)
Session: {purchase['stripe_session_id']}

Time: {purchase['created_at']}

Next steps:
- Buy Outright: ZIP the HTML and email it
- Hosted: Deploy to their domain
- Premium: Schedule kickoff call
"""

    email_raw = f"""From: freshsites@sites.propagate.media
To: {SUPPORT_EMAIL}
Subject: {subject}
Content-Type: text/plain; charset=utf-8

{body}
"""

    try:
        tmp = Path("/tmp") / f"freshsites_notification_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.eml"
        tmp.write_text(email_raw, encoding="utf-8")
        result = subprocess.run(
            [str(HIMALAYA_BIN), "message", "send", "--account", "freshsites"],
            input=tmp.read_text(),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print(f"  Notification sent to {SUPPORT_EMAIL}")
        else:
            print(f"  Notification failed: {result.stderr}")
    except Exception as e:
        print(f"  Notification error: {e}")


def handle_checkout_completed(session: dict):
    """Process a completed checkout."""
    print(f"Processing checkout: {session['id']}")
    purchase = store_purchase(session)
    send_notification(purchase)
    print(f"  Delivery: {purchase['delivery_method']} (ETA: {TIERS.get(str(purchase['amount_pence']), {}).get('hours', 48)}h)")


def process_session(session_id: str):
    """Manually process a checkout session."""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid":
            handle_checkout_completed(session)
        else:
            print(f"Session not paid: {session.payment_status}")
    except Exception as e:
        print(f"Error: {e}")


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/webhook":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            try:
                event = json.loads(body)
                if event.get("type") == "checkout.session.completed":
                    handle_checkout_completed(event["data"]["object"])

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            except Exception as e:
                print(f"Webhook error: {e}")
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging
        pass


def run_server(port=8000):
    init_purchases_table()
    server = HTTPS(("", port), WebhookHandler)
    print(f"Webhook server running on port {port}")
    print(f"Webhook URL: http://YOUR_DOMAIN:{port}/webhook")
    print("Set this in Stripe Dashboard > Developers > Webhooks")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")


if __name__ == "__main__":
    init_purchases_table()

    if "--server" in sys.argv:
        port = 8000
        for i, arg in enumerate(sys.argv):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        run_server(port)
    elif "--session" in sys.argv:
        idx = sys.argv.index("--session")
        if idx + 1 < len(sys.argv):
            process_session(sys.argv[idx + 1])
        else:
            print("Usage: --session cs_test_xxx")
    else:
        print("Usage:")
        print("  webhook_handler.py --server [--port 8000]")
        print("  webhook_handler.py --session cs_test_xxx")
