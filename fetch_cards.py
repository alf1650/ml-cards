#!/usr/bin/env python3
"""
Fetch all products from ccgmarket.org Shopify API,
download images, convert MYR prices to SGD with 5-10% markup,
and update data.json.
"""

import json
import os
import random
import re
import time
import urllib.request

BASE_URL = "https://www.ccgmarket.org/products.json"
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

# MYR to SGD conversion rate (approximate)
MYR_TO_SGD = 0.30

# Rarity mapping based on card ID prefix
RARITY_MAP = {
    "C": ("C", "Common"),
    "CS": ("C", "Common"),
    "R": ("R", "Rare"),
    "RS": ("RS", "Rising Star"),
    "SSR": ("SSR", "Super Super Rare"),
    "UR": ("UR", "Ultra Rare"),
    "SP": ("SP", "Special"),
    "AR": ("AR", "Augmented Reality"),
    "QR": ("QR", "Quick Release"),
    "TR": ("TR", "Trainer"),
}


def fetch_all_products():
    """Fetch all products from the Shopify API, paginating through all pages."""
    all_products = []
    page = 1
    while True:
        url = f"{BASE_URL}?page={page}&limit=250"
        print(f"Fetching page {page}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
        products = data.get("products", [])
        if not products:
            break
        all_products.extend(products)
        print(f"  Got {len(products)} products (total: {len(all_products)})")
        page += 1
        time.sleep(0.5)  # Be polite
    return all_products


def extract_card_id(title):
    """Extract card ID like ML-AS-C003 or ML-AS-UR*031 from product title."""
    match = re.search(r"\(?(ML-[A-Z]+-[A-Z]+\*?\d+)\)?", title)
    if match:
        return match.group(1)
    return None


def extract_rarity(card_id):
    """Extract rarity code from card ID."""
    match = re.match(r"ML-[A-Z]+-([A-Z]+)\*?\d+", card_id)
    if match:
        code = match.group(1)
        if code in RARITY_MAP:
            return RARITY_MAP[code]
    return ("C", "Common")


def extract_hero_and_skin(title, card_id):
    """Extract hero name and skin from product title."""
    # Remove the card ID part
    clean = re.sub(r"\s*\(?" + re.escape(card_id) + r"\)?\s*", "", title).strip()
    # The format is typically "HERO Skin Name"
    parts = clean.split(" ", 1)
    if len(parts) == 2:
        hero = parts[0].title()
        skin = parts[1]
    else:
        hero = parts[0].title()
        skin = hero
    return hero, skin


def convert_price(myr_price):
    """Convert MYR price to SGD with random 5-10% markup."""
    sgd = float(myr_price) * MYR_TO_SGD
    markup = random.uniform(1.05, 1.10)  # 5-10% markup
    return round(sgd * markup, 2)


def download_image(url, filename):
    """Download image from URL to images directory."""
    filepath = os.path.join(IMAGES_DIR, filename)
    if os.path.exists(filepath):
        print(f"  Image already exists: {filename}")
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            with open(filepath, "wb") as f:
                f.write(resp.read())
        print(f"  Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"  Failed to download {filename}: {e}")
        return False


def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Load existing data to preserve any existing cards
    existing_cards = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            existing_data = json.load(f)
            for card in existing_data.get("cards", []):
                existing_cards[card["id"]] = card

    print("Fetching all products from ccgmarket.org...")
    products = fetch_all_products()
    print(f"\nTotal products found: {len(products)}")

    cards = []
    heroes_seen = set()

    for product in products:
        title = product.get("title", "")
        card_id = extract_card_id(title)
        if not card_id:
            print(f"  Skipping (no card ID): {title}")
            continue

        # Get price from first variant
        variants = product.get("variants", [])
        myr_price = variants[0].get("price", "0") if variants else "0"
        sgd_price = convert_price(myr_price)

        # Get image
        images = product.get("images", [])
        img_url = images[0].get("src", "") if images else ""

        hero, skin = extract_hero_and_skin(title, card_id)
        heroes_seen.add(hero)
        rarity, rarity_label = extract_rarity(card_id)

        # Determine image filename (sanitize asterisk for filesystem)
        img_ext = "png"
        safe_id = card_id.replace("*", "_")
        img_filename = f"{safe_id}.{img_ext}"

        # Check if we already have this card with existing image
        if card_id in existing_cards:
            existing = existing_cards[card_id]
            # Keep existing image file, just add price
            card_entry = {
                "id": card_id,
                "file": existing["file"],
                "hero": hero,
                "skin": skin,
                "rarity": rarity,
                "rarityLabel": rarity_label,
                "priceSGD": sgd_price,
                "priceMYR": float(myr_price),
            }
        else:
            # Download new image
            if img_url:
                success = download_image(img_url, img_filename)
                if not success:
                    img_filename = ""
            card_entry = {
                "id": card_id,
                "file": img_filename,
                "hero": hero,
                "skin": skin,
                "rarity": rarity,
                "rarityLabel": rarity_label,
                "priceSGD": sgd_price,
                "priceMYR": float(myr_price),
            }

        cards.append(card_entry)
        time.sleep(0.1)  # Be polite with image downloads

    # Sort cards by rarity order, then by card ID
    rarity_order = {"C": 0, "R": 1, "RS": 2, "SSR": 3, "UR": 4, "SP": 5, "AR": 6, "QR": 7, "TR": 8}
    cards.sort(key=lambda c: (rarity_order.get(c["rarity"], 99), c["id"]))

    # Remove duplicates (keep last seen, which has later page data)
    seen_ids = {}
    unique_cards = []
    for card in cards:
        if card["id"] not in seen_ids:
            seen_ids[card["id"]] = len(unique_cards)
            unique_cards.append(card)
        else:
            # Update existing
            unique_cards[seen_ids[card["id"]]] = card
    cards = unique_cards

    # Build output data
    output = {
        "hero": "All Heroes",
        "role": "Collection",
        "specialty": "MLBB Cards",
        "cards": cards,
    }

    with open(DATA_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Done! {len(cards)} cards saved to data.json")
    print(f"   Heroes: {', '.join(sorted(heroes_seen))}")
    print(f"   Prices converted from MYR → SGD with 5-10% markup")


if __name__ == "__main__":
    main()
