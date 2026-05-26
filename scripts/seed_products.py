#!/usr/bin/env python3
"""Seed 10 real saree products with categories via live API."""
import json, sys
import urllib.request, urllib.error

BASE = "http://localhost"
TOKEN = sys.argv[1] if len(sys.argv) > 1 else ""
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}


def api(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code


# ── 1. Create categories ──────────────────────────────────────────────────────
CATEGORIES = [
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

print("Creating categories...")
cat_ids = {}
for cat in CATEGORIES:
    resp, status = api("POST", ":8002/api/v1/categories", cat)
    if status in (200, 201):
        cat_ids[cat["name"]] = resp["category_id"]
        print(f"  ✓ {cat['name']} ({cat['type']})")
    elif status == 409:
        # Already exists — fetch it
        existing, _ = api("GET", f":8002/api/v1/categories?type={cat['type']}")
        for c in (existing if isinstance(existing, list) else []):
            if c.get("name") == cat["name"]:
                cat_ids[cat["name"]] = c["category_id"]
        print(f"  ~ {cat['name']} (already exists)")

# ── 2. Create 10 saree products ───────────────────────────────────────────────
PRODUCTS = [
    {
        "name": "Royal Banarasi Silk Bridal Saree",
        "description": "A stunning bridal saree crafted from pure Banarasi silk. Features intricate gold zari weaving with traditional floral motifs. The deep red colour symbolizes auspiciousness, making it perfect for wedding ceremonies. Comes with a matching blouse piece.",
        "price": "12500.00",
        "discount_percentage": "10.00",
        "stock_qty": 8,
        "sku": "BAN-SILK-001",
        "blouse_included": True,
        "fabric_description": "Pure Banarasi Silk, 6.3m saree + 0.8m blouse piece, Gold zari work",
        "care_instructions": "Dry clean only. Store in a muslin cloth. Avoid direct sunlight.",
        "categories": ["Silk", "Bridal", "Banarasi"],
    },
    {
        "name": "Kanjivaram Pure Silk Temple Border Saree",
        "description": "Traditional Kanjivaram silk saree from Tamil Nadu, known for its rich texture and vibrant colors. Features the iconic temple border design with peacock and elephant motifs woven in contrasting zari. A masterpiece of South Indian weaving tradition.",
        "price": "15000.00",
        "discount_percentage": "5.00",
        "stock_qty": 6,
        "sku": "KAN-SILK-001",
        "blouse_included": True,
        "fabric_description": "Pure Kanjivaram Silk, 6.3m saree + 0.8m blouse, Silver & Gold zari",
        "care_instructions": "Dry clean only. Air after every use. Fold in half before storing.",
        "categories": ["Silk", "Festive", "Kanjivaram"],
    },
    {
        "name": "Paithani Silk Saree with Peacock Motif",
        "description": "Authentic Paithani saree from Paithan, Maharashtra. Hand-woven with real silver and gold threads, featuring the signature peacock and lotus motifs. The oblique design in the pallu is the hallmark of genuine Paithani craftsmanship.",
        "price": "18000.00",
        "discount_percentage": "0.00",
        "stock_qty": 4,
        "sku": "PAI-SILK-001",
        "blouse_included": True,
        "fabric_description": "Pure Silk with gold and silver zari, 5.5m saree + 0.8m blouse",
        "care_instructions": "Dry clean only. Store in airtight bags with silica gel packets.",
        "categories": ["Silk", "Bridal", "Paithani"],
    },
    {
        "name": "Bandhani Tie-Dye Georgette Festive Saree",
        "description": "Vibrant Bandhani saree from Rajasthan using the traditional tie-dye technique. Thousands of tiny dots create beautiful patterns on lightweight georgette fabric. Perfect for Navratri, Diwali, and festive occasions. Light and easy to drape.",
        "price": "4200.00",
        "discount_percentage": "12.00",
        "stock_qty": 20,
        "sku": "BAN-GEO-001",
        "blouse_included": True,
        "fabric_description": "Georgette with Bandhani tie-dye work, 5.5m saree + 0.8m blouse",
        "care_instructions": "Hand wash in cold water. Do not wring. Dry in shade.",
        "categories": ["Georgette", "Festive", "Bandhani"],
    },
    {
        "name": "Pochampally Ikat Cotton Casual Saree",
        "description": "Authentic Pochampally Ikat saree from Telangana, featuring geometric diamond patterns created through the resist-dyeing technique before weaving. Made from breathable cotton, ideal for daily wear in warm climates. GI-tagged product.",
        "price": "2800.00",
        "discount_percentage": "0.00",
        "stock_qty": 30,
        "sku": "POC-COT-001",
        "blouse_included": False,
        "fabric_description": "Pure Cotton Ikat, 5.5m saree, Geometric double ikat pattern",
        "care_instructions": "Machine wash cold, gentle cycle. Tumble dry low. Iron on medium heat.",
        "categories": ["Cotton", "Casual", "Pochampally"],
    },
    {
        "name": "Chiffon Embroidered Party Wear Saree",
        "description": "Elegant lightweight chiffon saree with intricate thread embroidery along the border and pallu. The subtle shimmer of the fabric paired with delicate floral embroidery makes it perfect for cocktail parties and evening events.",
        "price": "3500.00",
        "discount_percentage": "15.00",
        "stock_qty": 18,
        "sku": "CHI-EMB-001",
        "blouse_included": True,
        "fabric_description": "Chiffon with thread embroidery, 5.5m saree + 0.8m embroidered blouse",
        "care_instructions": "Dry clean recommended. Hand wash gently if needed.",
        "categories": ["Chiffon", "Party"],
    },
    {
        "name": "Chanderi Silk Cotton Office Wear Saree",
        "description": "Graceful Chanderi saree from Madhya Pradesh blending silk and cotton for the perfect balance of elegance and comfort. Features delicate golden buti (small motifs) on a sheer fabric. Professional enough for the workplace, beautiful enough for events.",
        "price": "3200.00",
        "discount_percentage": "8.00",
        "stock_qty": 25,
        "sku": "CHA-SLK-001",
        "blouse_included": False,
        "fabric_description": "Chanderi Silk Cotton blend, 5.5m saree, Gold buti work",
        "care_instructions": "Dry clean preferred. Hand wash with mild soap if needed.",
        "categories": ["Chanderi", "Office"],
    },
    {
        "name": "Banarasi Georgette Designer Party Saree",
        "description": "Contemporary fusion saree combining Banarasi weaving artistry with lightweight georgette base. Features modern floral patterns in gold zari on a pastel background. Perfect for sangeet, reception, and high-end parties.",
        "price": "6500.00",
        "discount_percentage": "20.00",
        "stock_qty": 12,
        "sku": "BAN-GEO-002",
        "blouse_included": True,
        "fabric_description": "Georgette with Banarasi zari weaving, 5.5m saree + 0.8m blouse",
        "care_instructions": "Dry clean only.",
        "categories": ["Georgette", "Party", "Banarasi"],
    },
    {
        "name": "Cotton Tant Casual Everyday Saree",
        "description": "Comfortable and lightweight pure cotton Tant saree from West Bengal. Perfect for everyday wear with its soft texture and easy drape. The simple stripe and check patterns in natural cotton colours are timeless classics.",
        "price": "1200.00",
        "discount_percentage": "0.00",
        "stock_qty": 50,
        "sku": "COT-TAN-001",
        "blouse_included": False,
        "fabric_description": "Pure Cotton Tant, 5.5m saree, Stripe and check patterns",
        "care_instructions": "Machine washable. Iron while slightly damp for best results.",
        "categories": ["Cotton", "Casual"],
    },
    {
        "name": "Kanjivaram Silk Bridal Wedding Collection",
        "description": "Premium bridal Kanjivaram saree with heavy gold zari work throughout the body and pallu. The traditional checks pattern with korvai (interlocked warp threads joining the border to the body) is the signature of authentic Kanjivaram. A once-in-a-lifetime saree for a once-in-a-lifetime occasion.",
        "price": "22000.00",
        "discount_percentage": "5.00",
        "stock_qty": 3,
        "sku": "KAN-BRI-001",
        "blouse_included": True,
        "fabric_description": "Pure Kanjivaram Silk, 6.3m saree + 0.8m blouse, Heavy gold zari throughout",
        "care_instructions": "Dry clean only by experienced silk saree cleaners only. Store in pure cotton cloth.",
        "categories": ["Silk", "Bridal", "Kanjivaram"],
    },
]

print("\nCreating products...")
for p in PRODUCTS:
    # Resolve category IDs
    cat_id_list = [cat_ids[c] for c in p.pop("categories") if c in cat_ids]
    p["category_ids"] = cat_id_list
    resp, status = api("POST", ":8002/api/v1/products", p)
    if status in (200, 201):
        print(f"  ✓ {p['name'][:55]}... ₹{p['price']}")
    elif status == 409:
        print(f"  ~ {p['name'][:55]}... (already exists)")
    else:
        print(f"  ✗ {p['name'][:55]}... FAILED {status}: {str(resp)[:80]}")

print("\nDone! Visit http://localhost:5173/sarees to see your products.")
