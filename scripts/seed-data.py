#!/usr/bin/env python3
"""
seed-data.py — Create initial data for local development.

Creates:
  1. Admin user (admin@sabhyakriti.com / Admin@123!)
  2. Sample saree categories (Fabric + Occasion + Region)
  3. 6 sample saree products with images

Run after start-local.sh with all services healthy.
"""
import json
import sys
import time

import httpx

BASE = "http://localhost"
INTERNAL_SECRET = "local-dev-secret-change-in-prod"

client = httpx.Client(timeout=15.0)


def wait_for_service(url: str, name: str, retries: int = 10) -> None:
    for i in range(retries):
        try:
            r = client.get(url)
            if r.status_code == 200:
                print(f"  {name}: ready")
                return
        except Exception:
            pass
        print(f"  Waiting for {name}... ({i+1}/{retries})")
        time.sleep(3)
    print(f"  ERROR: {name} not available after {retries} attempts")
    sys.exit(1)


def register_admin() -> str:
    """Register admin user and return access token."""
    print("\n==> Creating admin user...")

    # Register
    r = client.post(f"{BASE}:8001/api/v1/auth/register", json={
        "email": "admin@sabhyakriti.com",
        "password": "Admin@123!",
        "full_name": "Sabhyakriti Admin",
    })
    if r.status_code == 409:
        print("  Admin user already exists.")
    elif r.status_code == 201:
        print("  Registered admin@sabhyakriti.com")
        print("  NOTE: In dev mode, check auth-service logs for the verification link.")
        print("        Or query the DB: SELECT token_hash FROM auth.email_verification_tokens LIMIT 1;")
        print("        Then call: GET http://localhost:8001/api/v1/auth/verify-email?token=<raw_token>")
    else:
        print(f"  Register response: {r.status_code} {r.text}")

    # For seeding, directly update the user role via DB — or use the internal endpoint
    # In a real setup you'd verify email; for local dev we'll note this limitation
    print("  ACTION: Verify admin email before logging in (check auth-service logs for token).")
    return ""


def seed_categories(token: str) -> dict[str, str]:
    """Create all saree categories. Returns {name: category_id}."""
    print("\n==> Seeding categories...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    ids: dict[str, str] = {}

    categories = [
        # Fabric
        {"name": "Silk", "type": "FABRIC", "display_order": 1},
        {"name": "Cotton", "type": "FABRIC", "display_order": 2},
        {"name": "Georgette", "type": "FABRIC", "display_order": 3},
        {"name": "Chiffon", "type": "FABRIC", "display_order": 4},
        {"name": "Chanderi", "type": "FABRIC", "display_order": 5},
        # Occasion
        {"name": "Bridal", "type": "OCCASION", "display_order": 1},
        {"name": "Party", "type": "OCCASION", "display_order": 2},
        {"name": "Casual", "type": "OCCASION", "display_order": 3},
        {"name": "Festive", "type": "OCCASION", "display_order": 4},
        {"name": "Office", "type": "OCCASION", "display_order": 5},
        # Region
        {"name": "Banarasi", "type": "REGION", "display_order": 1},
        {"name": "Kanjivaram", "type": "REGION", "display_order": 2},
        {"name": "Bandhani", "type": "REGION", "display_order": 3},
        {"name": "Pochampally", "type": "REGION", "display_order": 4},
        {"name": "Paithani", "type": "REGION", "display_order": 5},
    ]

    for cat in categories:
        r = client.post(f"{BASE}:8002/api/v1/categories", json=cat, headers=headers)
        if r.status_code in (200, 201):
            data = r.json()
            ids[cat["name"]] = data["category_id"]
            print(f"  Created category: {cat['name']} ({cat['type']})")
        elif r.status_code == 409:
            # Already exists — fetch it
            cats = client.get(f"{BASE}:8002/api/v1/categories?type={cat['type']}").json()
            for c in cats:
                if c["name"] == cat["name"]:
                    ids[cat["name"]] = c["category_id"]
                    break
        else:
            print(f"  WARNING: Could not create {cat['name']}: {r.status_code}")

    return ids


def seed_products(token: str, category_ids: dict[str, str]) -> None:
    """Create 6 sample sarees."""
    print("\n==> Seeding sample products...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    products = [
        {
            "name": "Banarasi Silk Red Bridal Saree",
            "description": "Exquisite pure Banarasi silk saree with intricate zari work. Perfect for weddings and grand celebrations.",
            "price": "8500.00",
            "discount_percentage": "10.00",
            "stock_qty": 15,
            "sku": "SKU-BAN-001",
            "blouse_included": True,
            "fabric_description": "Pure Banarasi Silk, 6.3m saree + 0.8m blouse",
            "care_instructions": "Dry clean only. Store in a cool, dry place.",
            "category_ids": [
                category_ids.get("Silk"), category_ids.get("Bridal"), category_ids.get("Banarasi"),
            ],
        },
        {
            "name": "Kanjivaram Pure Silk Blue Saree",
            "description": "Traditional Kanjivaram silk with temple border design. A masterpiece of South Indian weaving.",
            "price": "12000.00",
            "discount_percentage": "5.00",
            "stock_qty": 8,
            "sku": "SKU-KAN-001",
            "blouse_included": True,
            "fabric_description": "Pure Kanjivaram Silk, 6.3m saree + 0.8m blouse",
            "care_instructions": "Dry clean only. Air after every use.",
            "category_ids": [
                category_ids.get("Silk"), category_ids.get("Festive"), category_ids.get("Kanjivaram"),
            ],
        },
        {
            "name": "Georgette Party Wear Saree",
            "description": "Lightweight georgette saree with beautiful embroidery. Ideal for parties and evening events.",
            "price": "3200.00",
            "discount_percentage": "15.00",
            "stock_qty": 25,
            "sku": "SKU-GEO-001",
            "blouse_included": True,
            "fabric_description": "Georgette, 5.5m saree + 0.8m blouse",
            "care_instructions": "Hand wash with mild detergent.",
            "category_ids": [
                category_ids.get("Georgette"), category_ids.get("Party"),
            ],
        },
        {
            "name": "Cotton Casual Daily Wear Saree",
            "description": "Comfortable pure cotton saree for daily wear. Breathable and easy to drape.",
            "price": "1200.00",
            "discount_percentage": "0.00",
            "stock_qty": 50,
            "sku": "SKU-COT-001",
            "blouse_included": False,
            "fabric_description": "Pure Cotton, 5.5m saree",
            "care_instructions": "Machine wash cold. Tumble dry low.",
            "category_ids": [
                category_ids.get("Cotton"), category_ids.get("Casual"),
            ],
        },
        {
            "name": "Bandhani Festive Silk Saree",
            "description": "Vibrant Bandhani pattern on silk. Celebrate festivals in style.",
            "price": "4500.00",
            "discount_percentage": "8.00",
            "stock_qty": 12,
            "sku": "SKU-BAN-002",
            "blouse_included": True,
            "fabric_description": "Silk with Bandhani work, 6m saree + 0.8m blouse",
            "care_instructions": "Dry clean recommended.",
            "category_ids": [
                category_ids.get("Silk"), category_ids.get("Festive"), category_ids.get("Bandhani"),
            ],
        },
        {
            "name": "Chiffon Office Wear Saree",
            "description": "Elegant solid chiffon saree perfect for professional settings.",
            "price": "2800.00",
            "discount_percentage": "12.00",
            "stock_qty": 30,
            "sku": "SKU-CHI-001",
            "blouse_included": True,
            "fabric_description": "Chiffon, 5.5m saree + 0.8m blouse",
            "care_instructions": "Dry clean only.",
            "category_ids": [
                category_ids.get("Chiffon"), category_ids.get("Office"),
            ],
        },
    ]

    for product in products:
        # Filter out None category IDs
        product["category_ids"] = [c for c in product["category_ids"] if c]
        r = client.post(f"{BASE}:8002/api/v1/products", json=product, headers=headers)
        if r.status_code in (200, 201):
            print(f"  Created: {product['name']}")
        elif r.status_code == 409:
            print(f"  Already exists: {product['name']}")
        else:
            print(f"  WARNING: Could not create {product['name']}: {r.status_code} {r.text[:100]}")


def main() -> None:
    print("Sabhyakriti Local Development Seed Script")
    print("=" * 50)

    # Wait for services
    print("\n==> Checking services...")
    wait_for_service(f"{BASE}:8001/health", "auth-service")
    wait_for_service(f"{BASE}:8002/health", "product-service")

    # Create admin
    register_admin()

    print("\n  IMPORTANT: You must verify the admin email before continuing.")
    print("  Check the auth-service container logs for the verification link:")
    print("    docker compose -f docker-compose.all.yml logs auth-service | grep 'verify'")
    print("")
    input("  Press Enter once admin email is verified and you have an admin JWT token...")
    admin_token = input("  Paste admin JWT access_token: ").strip()

    if not admin_token:
        print("  Skipping category/product seeding (no token provided).")
        print("  Re-run this script after logging in as admin.")
        return

    # Seed categories and products
    category_ids = seed_categories(admin_token)
    seed_products(admin_token, category_ids)

    print("\n" + "=" * 50)
    print("  Seeding complete!")
    print("  Open http://localhost:5173 to browse the platform.")
    print("  Admin panel: http://localhost:5173/admin")


if __name__ == "__main__":
    main()
