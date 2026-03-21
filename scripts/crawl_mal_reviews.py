"""
Crawl MAL reviews for all Keroro Gunso related anime/manga using Jikan API v4.
Saves raw JSON responses to files first, then parses and inserts into DB.
Handles rate limiting (1 second between requests).
"""

import json
import os
import sqlite3
import time
import urllib.request
import urllib.error
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "keroro.db")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# All Keroro-related anime/manga IDs from MAL
ANIME_IDS = {
    516: "Keroro Gunsou (TV)",
    21671: "Keroro (2014 TV)",
    2407: "Keroro Gunsou Movie 1",
    2408: "Keroro Gunsou Movie 2",
    5290: "Keroro Gunsou Movie 3",
    5710: "Keroro Gunsou Movie 4",
    8134: "Keroro Gunsou Movie 5",
    58773: "Keroro Gunsou Movie 6",
    11299: "Kero 0: Shuppatsu da yo!",
    11281: "Keroro Gunsou: Mushakero Ohirome",
    5449: "Chibi Kero",
    63157: "Keroro Gunsou (2025 TV)",
    50662: "Keroro x No More Eiga Dorobou",
    54355: "Keroro Gunsou Chou Rittai-ban",
}

MANGA_IDS = {
    390: "Keroro Gunsou (Manga)",
}

JIKAN_BASE = "https://api.jikan.moe/v4"
REQUEST_DELAY = 1.2  # seconds between requests (Jikan rate limit: 3 req/sec, be safe)


def fetch_json(url, output_path):
    """Fetch URL and save raw JSON to file. Returns parsed dict or None on error."""
    print(f"  Fetching: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KereroArchiveCrawler/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
        # Save raw bytes to file
        with open(output_path, "wb") as f:
            f.write(raw)
        # Parse as UTF-8 JSON
        return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        if e.code == 429:
            print("  Rate limited! Waiting 5 seconds...")
            time.sleep(5)
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def crawl_reviews(media_type, media_id, media_name):
    """Crawl all review pages for given anime/manga."""
    all_reviews = []
    page = 1

    while True:
        url = f"{JIKAN_BASE}/{media_type}/{media_id}/reviews?page={page}"
        filename = f"jikan_{media_type}_{media_id}_reviews_p{page}.json"
        output_path = os.path.join(DATA_DIR, filename)

        data = fetch_json(url, output_path)
        time.sleep(REQUEST_DELAY)

        if data is None:
            print(f"  Failed to fetch page {page}, stopping.")
            break

        reviews = data.get("data", [])
        if not reviews:
            print(f"  No reviews on page {page}.")
            break

        print(f"  Got {len(reviews)} reviews from page {page}")

        for r in reviews:
            all_reviews.append({
                "mal_id": r["mal_id"],
                "username": r.get("user", {}).get("username", ""),
                "score": r.get("score"),
                "date": r.get("date", ""),
                "review": r.get("review", ""),
                "tags": json.dumps(r.get("tags", []), ensure_ascii=False),
                "episodes_watched": r.get("episodes_watched"),
                "is_spoiler": 1 if r.get("is_spoiler") else 0,
                "is_preliminary": 1 if r.get("is_preliminary") else 0,
                "reactions_json": json.dumps(r.get("reactions", {}), ensure_ascii=False),
                "source_type": media_type,
                "source_mal_id": media_id,
                "source_name": media_name,
            })

        pagination = data.get("pagination", {})
        if not pagination.get("has_next_page", False):
            break
        page += 1

    return all_reviews


def ensure_columns(conn):
    """Add source tracking columns if they don't exist."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(mal_reviews)")
    existing_cols = {col[1] for col in cursor.fetchall()}

    new_cols = {
        "source_type": "TEXT DEFAULT 'anime'",
        "source_mal_id": "INTEGER DEFAULT 516",
        "source_name": "TEXT DEFAULT ''",
    }

    for col_name, col_def in new_cols.items():
        if col_name not in existing_cols:
            print(f"Adding column: {col_name}")
            cursor.execute(f"ALTER TABLE mal_reviews ADD COLUMN {col_name} {col_def}")

    conn.commit()

    # Update existing records that don't have source info
    cursor.execute(
        "UPDATE mal_reviews SET source_type='anime', source_mal_id=516, "
        "source_name='Keroro Gunsou (TV)' WHERE source_name IS NULL OR source_name=''"
    )
    conn.commit()


def insert_reviews(conn, reviews):
    """Insert reviews, skipping duplicates by mal_id."""
    cursor = conn.cursor()

    # Get existing mal_ids
    cursor.execute("SELECT mal_id FROM mal_reviews")
    existing_ids = {row[0] for row in cursor.fetchall()}

    inserted = 0
    skipped = 0

    for r in reviews:
        if r["mal_id"] in existing_ids:
            skipped += 1
            continue

        cursor.execute("""
            INSERT INTO mal_reviews
            (mal_id, username, score, date, review, tags, episodes_watched,
             is_spoiler, is_preliminary, reactions_json, source_type, source_mal_id, source_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["mal_id"], r["username"], r["score"], r["date"], r["review"],
            r["tags"], r["episodes_watched"], r["is_spoiler"], r["is_preliminary"],
            r["reactions_json"], r["source_type"], r["source_mal_id"], r["source_name"],
        ))
        existing_ids.add(r["mal_id"])
        inserted += 1

    conn.commit()
    return inserted, skipped


def main():
    print("=== Keroro MAL Reviews Crawler ===")
    print(f"Database: {os.path.abspath(DB_PATH)}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    conn = sqlite3.connect(DB_PATH)
    ensure_columns(conn)

    # Get initial count
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mal_reviews")
    initial_count = cursor.fetchone()[0]
    print(f"Initial review count: {initial_count}")
    print()

    all_reviews = []

    # Crawl anime reviews
    print("=== Crawling Anime Reviews ===")
    for mal_id, name in ANIME_IDS.items():
        print(f"\n[Anime {mal_id}] {name}")
        reviews = crawl_reviews("anime", mal_id, name)
        all_reviews.extend(reviews)
        print(f"  Total collected: {len(reviews)}")

    # Crawl manga reviews
    print("\n=== Crawling Manga Reviews ===")
    for mal_id, name in MANGA_IDS.items():
        print(f"\n[Manga {mal_id}] {name}")
        reviews = crawl_reviews("manga", mal_id, name)
        all_reviews.extend(reviews)
        print(f"  Total collected: {len(reviews)}")

    # Insert into DB
    print("\n=== Inserting Reviews ===")
    print(f"Total crawled: {len(all_reviews)}")
    inserted, skipped = insert_reviews(conn, all_reviews)
    print(f"Inserted: {inserted}, Skipped (duplicates): {skipped}")

    # Final count
    cursor.execute("SELECT COUNT(*) FROM mal_reviews")
    final_count = cursor.fetchone()[0]
    print("\n=== Final Summary ===")
    print(f"Before: {initial_count} reviews")
    print(f"After:  {final_count} reviews")
    print(f"New:    {final_count - initial_count} reviews added")

    # Show breakdown by source
    cursor.execute("""
        SELECT source_type, source_mal_id, source_name, COUNT(*) as cnt
        FROM mal_reviews
        GROUP BY source_type, source_mal_id
        ORDER BY cnt DESC
    """)
    print("\n=== Reviews by Source ===")
    for row in cursor.fetchall():
        print(f"  {row[0]:>5} {row[1]:>6} | {row[3]:>3} reviews | {row[2]}")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
