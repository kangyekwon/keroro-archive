"""
Update characters.json image_url fields with real MAL CDN image URLs.

Reads mal_characters.json (crawled from MyAnimeList) and fuzzy-matches
character names to our characters.json, then updates image_url fields
with the real MAL CDN URLs.

Matching strategy:
1. Exact case-insensitive match on English name
2. Reversed MAL name ("Last, First" -> "First Last") match
3. Partial substring match (MAL name contained in our name or vice versa)
4. Special hardcoded mappings for tricky cases
"""

import io
import json
import os
import sys

# Fix Windows console encoding for special characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MAL_FILE = os.path.join(DATA_DIR, "crawled", "mal_characters.json")
CHARACTERS_FILE = os.path.join(DATA_DIR, "characters.json")


def load_json(filepath: str) -> list:
    """Load a JSON file and return its contents."""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath: str, data: list) -> None:
    """Save data to a JSON file with pretty formatting."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_name(name: str) -> str:
    """Normalize a character name for comparison."""
    # Remove periods, extra whitespace, lowercase
    return name.strip().lower().replace(".", "").replace("'", "'").strip()


def reverse_mal_name(mal_name: str) -> str:
    """Convert MAL 'Last, First' format to 'First Last'."""
    if "," in mal_name:
        parts = mal_name.split(",", 1)
        return f"{parts[1].strip()} {parts[0].strip()}"
    return mal_name


# Special hardcoded mappings for names that cannot be matched automatically.
# Key: normalized MAL name, Value: our character English name
SPECIAL_MAPPINGS = {
    "man, dance": "Dasonu Maso",
    "maso, dansonu": "Dasonu Maso",
    "saburo, mutsumi": "Saburo",
    "father, giroro and garuru's": "Garuru and Giroro's Father",
    "fear, angol": None,  # Angol Fear - not in our DB
    "goa, angol": "Angol God",
    "gray, r": None,  # R Gray - not in our DB
    "nakata, joji": None,  # Meta character (voice actor cameo)
    "watanabe, kumiko": None,  # Meta character (voice actor cameo)
    "nadeshiko, yamato": None,  # Not in our DB
    "honey, melody": None,  # Melody Honey - not in our DB
    "harpie, jessica": None,  # Jessica Harpie - not in our DB
    "hinata, akina": None,  # Akina Hinata (grandmother) - not in our DB
    "imogo, rie": None,  # Rie Imogo - not in our DB
    "kinoshita, rei": None,  # Rei Kinoshita - not in our DB
    "yoshiokadaira, masayoshi": None,  # Not in our DB
    "shimotsuki, yayoi": None,  # Not in our DB
    "shiwasu, satsuki": None,  # Not in our DB
    "narrator": "Narrator",
    "kiruru": "Kiruru",
}


def find_match(mal_char: dict, our_chars: list) -> dict | None:
    """
    Find the best matching character from our DB for a MAL character.
    Returns the matching character dict or None.
    """
    mal_name = mal_char["name"]
    mal_norm = normalize_name(mal_name)

    # Check special mappings first
    if mal_norm in SPECIAL_MAPPINGS:
        target_name = SPECIAL_MAPPINGS[mal_norm]
        if target_name is None:
            return None
        for c in our_chars:
            if c["name"].lower() == target_name.lower():
                return c
        return None

    # Strategy 1: Exact match on normalized name
    for c in our_chars:
        if normalize_name(c["name"]) == mal_norm:
            return c

    # Strategy 2: Reversed MAL name match ("Hinata, Natsumi" -> "Natsumi Hinata")
    reversed_name = normalize_name(reverse_mal_name(mal_name))
    for c in our_chars:
        if normalize_name(c["name"]) == reversed_name:
            return c

    # Strategy 3: Handle possessive forms ("Keroro's mother" -> "Keroro's Mother")
    for c in our_chars:
        c_norm = normalize_name(c["name"])
        if mal_norm == c_norm:
            return c
        # Check if one contains the other (for possessive/family names)
        if "'s " in mal_norm and "'s " in c_norm:
            # Both have possessive - compare
            mal_base = mal_norm.replace("'s mother", "").replace("'s father", "")
            c_base = c_norm.replace("'s mother", "").replace("'s father", "")
            if mal_base == c_base and (
                ("mother" in mal_norm and "mother" in c_norm)
                or ("father" in mal_norm and "father" in c_norm)
            ):
                return c

    # Strategy 4: Partial match - MAL single name matches our name start/end
    # Only for single-word MAL names (no comma)
    if "," not in mal_name and " " not in mal_name.strip():
        mal_word = mal_norm
        best_match = None
        best_score = 0
        for c in our_chars:
            c_norm = normalize_name(c["name"])
            # Exact single word match (e.g., "Keroro" == "Keroro")
            if c_norm == mal_word:
                return c
            # Check if the MAL name is a word in our character name
            c_words = c_norm.replace("(", "").replace(")", "").split()
            if mal_word in c_words:
                # Prefer shorter names (more specific match)
                score = 1.0 / len(c_norm)
                if score > best_score:
                    best_score = score
                    best_match = c
        if best_match:
            return best_match

    # Strategy 5: Reversed name partial match
    if "," in mal_name:
        reversed_parts = reverse_mal_name(mal_name).lower().split()
        for c in our_chars:
            c_words = normalize_name(c["name"]).split()
            # Check if all reversed parts appear in our character name
            if all(rp in c_words for rp in reversed_parts):
                return c

    return None


def is_valid_image_url(url: str) -> bool:
    """Check if a MAL image URL is a real character image (not a placeholder)."""
    if not url:
        return False
    # MAL uses questionmark_23.gif for characters without images
    if "questionmark" in url:
        return False
    return True


def main():
    """Main function to update character images."""
    print("=" * 60)
    print("Keroro Archive - MAL Image URL Updater")
    print("=" * 60)

    # Load data
    if not os.path.exists(MAL_FILE):
        print(f"ERROR: MAL characters file not found: {MAL_FILE}")
        sys.exit(1)
    if not os.path.exists(CHARACTERS_FILE):
        print(f"ERROR: Characters file not found: {CHARACTERS_FILE}")
        sys.exit(1)

    mal_chars = load_json(MAL_FILE)
    our_chars = load_json(CHARACTERS_FILE)

    print(f"\nMAL characters loaded: {len(mal_chars)}")
    print(f"Our characters loaded: {len(our_chars)}")
    print()

    # Track results
    matched = []
    unmatched_mal = []
    no_valid_image = []
    updated_count = 0

    for mal_char in mal_chars:
        mal_name = mal_char["name"]
        mal_image = mal_char.get("image_url", "")

        match = find_match(mal_char, our_chars)

        if match is None:
            unmatched_mal.append(mal_name)
            continue

        if not is_valid_image_url(mal_image):
            no_valid_image.append((mal_name, match["name"]))
            continue

        matched.append((mal_name, match["name"], mal_image))

        # Update the image_url in our character data
        for c in our_chars:
            if c["id"] == match["id"]:
                old_url = c.get("image_url", "")
                c["image_url"] = mal_image
                updated_count += 1
                print(f"  [UPDATED] {match['name']} (id={match['id']})")
                print(f"    MAL name: {mal_name}")
                print(f"    Old: {old_url}")
                print(f"    New: {mal_image}")
                break

    # Save updated characters.json
    save_json(CHARACTERS_FILE, our_chars)

    # Print summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total MAL characters:     {len(mal_chars)}")
    print(f"  Successfully matched:     {len(matched)}")
    print(f"  Updated image URLs:       {updated_count}")
    print(f"  No valid MAL image:       {len(no_valid_image)}")
    print(f"  Unmatched MAL characters: {len(unmatched_mal)}")

    if no_valid_image:
        print("\n  Characters matched but MAL has placeholder image:")
        for mal_name, our_name in no_valid_image:
            print(f"    - {mal_name} -> {our_name}")

    if unmatched_mal:
        print("\n  MAL characters not matched to our DB:")
        for name in unmatched_mal:
            print(f"    - {name}")

    # Count characters still using SVG avatars
    svg_count = sum(1 for c in our_chars if c.get("image_url", "").endswith(".svg"))
    mal_count = sum(1 for c in our_chars if "cdn.myanimelist.net" in c.get("image_url", ""))
    print("\n  Final image stats:")
    print(f"    MAL CDN images: {mal_count}")
    print(f"    SVG avatars:    {svg_count}")
    print(f"    Total:          {len(our_chars)}")

    print("\ncharacters.json saved successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
