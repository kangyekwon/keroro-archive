"""
Jikan API (MyAnimeList) Crawler for Keroro Gunso Archive.

Fetches real data from MAL via the Jikan v4 API:
- Anime details (score, rank, popularity, members, synopsis)
- Character data (favorites, roles)
- Episode list with titles and aired dates
- User reviews (score, text)
- Score distribution statistics
- Recommendations

Usage:
    python -m crawler.mal_crawler [--full] [--characters] [--episodes] [--reviews] [--stats]
"""

import json
import logging
import os
import sqlite3
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CRAWLED_DIR = os.path.join(DATA_DIR, "crawled")

JIKAN_BASE = "https://api.jikan.moe/v4"

# Keroro Gunso MAL IDs
MAL_IDS = {
    "tv": 516,          # Main TV series (358 eps, 2004-2011)
    "tv_new": 63157,    # New TV series (2026)
    "movie1": 2407,     # Movie 1 (2006)
    "movie2": 2408,     # Movie 2 (2007)
    "movie3": 5290,     # Movie 3 (2008)
    "movie4": 5710,     # Movie 4 (2009)
    "movie5": 8134,     # Movie 5 (2010)
    "movie6": 58773,    # Movie 6 (2026, upcoming)
}

# Rate limit: Jikan allows ~3 requests/second, we'll be conservative
RATE_LIMIT_SECONDS = 1.2


def _fetch_json(url: str, retries: int = 3) -> dict | None:
    """Fetch JSON from URL with retry and rate limiting."""
    for attempt in range(retries):
        try:
            time.sleep(RATE_LIMIT_SECONDS)
            req = Request(url, headers={"User-Agent": "KeroroArchive/1.0"})
            with urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except HTTPError as e:
            if e.code == 429:
                wait = 4 * (attempt + 1)
                logger.warning("Rate limited (429). Waiting %ds...", wait)
                time.sleep(wait)
            elif e.code == 404:
                logger.warning("Not found (404): %s", url)
                return None
            else:
                logger.error("HTTP %d for %s", e.code, url)
                time.sleep(2)
        except (URLError, TimeoutError) as e:
            logger.warning("Connection error (attempt %d/%d): %s", attempt + 1, retries, e)
            time.sleep(3)
        except json.JSONDecodeError as e:
            logger.error("JSON decode error: %s", e)
            return None
    return None


def crawl_anime_details() -> list[dict]:
    """Fetch basic details for all Keroro anime entries."""
    results = []
    for key, mal_id in MAL_IDS.items():
        logger.info("Fetching anime details for %s (MAL ID: %d)...", key, mal_id)
        data = _fetch_json(f"{JIKAN_BASE}/anime/{mal_id}/full")
        if data and "data" in data:
            d = data["data"]
            entry = {
                "mal_id": d.get("mal_id"),
                "title": d.get("title", ""),
                "title_english": d.get("title_english", ""),
                "title_japanese": d.get("title_japanese", ""),
                "type": d.get("type", ""),
                "episodes": d.get("episodes"),
                "status": d.get("status", ""),
                "score": d.get("score"),
                "scored_by": d.get("scored_by"),
                "rank": d.get("rank"),
                "popularity": d.get("popularity"),
                "members": d.get("members"),
                "favorites": d.get("favorites"),
                "synopsis": d.get("synopsis", ""),
                "season": d.get("season", ""),
                "year": d.get("year"),
                "rating": d.get("rating", ""),
                "duration": d.get("duration", ""),
                "aired_from": d.get("aired", {}).get("from", ""),
                "aired_to": d.get("aired", {}).get("to", ""),
                "studios": ", ".join(s["name"] for s in d.get("studios", [])),
                "genres": ", ".join(g["name"] for g in d.get("genres", [])),
                "themes": ", ".join(t["name"] for t in d.get("themes", [])),
                "demographics": ", ".join(dm["name"] for dm in d.get("demographics", [])),
                "image_url": d.get("images", {}).get("jpg", {}).get("large_image_url", ""),
                "key": key,
            }
            results.append(entry)
            logger.info("  -> %s | Score: %s | Members: %s", entry["title"], entry["score"], entry["members"])
    return results


def crawl_characters(mal_id: int = 516) -> list[dict]:
    """Fetch character data with popularity/favorites from MAL."""
    logger.info("Fetching characters for MAL ID %d...", mal_id)
    data = _fetch_json(f"{JIKAN_BASE}/anime/{mal_id}/characters")
    if not data or "data" not in data:
        return []

    results = []
    for item in data["data"]:
        char = item.get("character", {})
        entry = {
            "mal_id": char.get("mal_id"),
            "name": char.get("name", ""),
            "image_url": char.get("images", {}).get("jpg", {}).get("image_url", ""),
            "favorites": item.get("favorites", 0),
            "role": item.get("role", ""),
            "voice_actors": [],
        }
        for va in item.get("voice_actors", []):
            person = va.get("person", {})
            entry["voice_actors"].append({
                "mal_id": person.get("mal_id"),
                "name": person.get("name", ""),
                "language": va.get("language", ""),
                "image_url": person.get("images", {}).get("jpg", {}).get("image_url", ""),
            })
        results.append(entry)

    results.sort(key=lambda x: x["favorites"], reverse=True)
    logger.info("  -> Found %d characters", len(results))
    return results


def crawl_episodes(mal_id: int = 516) -> list[dict]:
    """Fetch all episodes with pagination from MAL."""
    logger.info("Fetching episodes for MAL ID %d...", mal_id)
    all_episodes = []
    page = 1
    has_next = True

    while has_next:
        data = _fetch_json(f"{JIKAN_BASE}/anime/{mal_id}/episodes?page={page}")
        if not data or "data" not in data:
            break
        episodes = data["data"]
        if not episodes:
            break

        for ep in episodes:
            all_episodes.append({
                "mal_id": ep.get("mal_id"),
                "title": ep.get("title", ""),
                "title_japanese": ep.get("title_japanese", ""),
                "title_romanji": ep.get("title_romanji", ""),
                "aired": ep.get("aired", ""),
                "score": ep.get("score"),
                "filler": ep.get("filler", False),
                "recap": ep.get("recap", False),
            })

        has_next = data.get("pagination", {}).get("has_next_page", False)
        page += 1
        logger.info("  -> Page %d: %d episodes (total so far: %d)", page - 1, len(episodes), len(all_episodes))

    logger.info("  -> Total episodes fetched: %d", len(all_episodes))
    return all_episodes


def crawl_reviews(mal_id: int = 516, pages: int = 3) -> list[dict]:
    """Fetch user reviews from MAL."""
    logger.info("Fetching reviews for MAL ID %d (%d pages)...", mal_id, pages)
    all_reviews = []

    for page in range(1, pages + 1):
        data = _fetch_json(f"{JIKAN_BASE}/anime/{mal_id}/reviews?page={page}")
        if not data or "data" not in data:
            break

        for rev in data["data"]:
            user = rev.get("user", {})
            all_reviews.append({
                "mal_id": rev.get("mal_id"),
                "username": user.get("username", ""),
                "score": rev.get("score"),
                "date": rev.get("date", ""),
                "review": rev.get("review", "")[:2000],
                "tags": [t for t in rev.get("tags", [])],
                "episodes_watched": rev.get("episodes_watched"),
                "is_spoiler": rev.get("is_spoiler", False),
                "is_preliminary": rev.get("is_preliminary", False),
                "reactions": rev.get("reactions", {}),
            })

        if not data.get("pagination", {}).get("has_next_page", False):
            break

    logger.info("  -> Fetched %d reviews", len(all_reviews))
    return all_reviews


def crawl_statistics(mal_id: int = 516) -> dict:
    """Fetch score distribution and viewing statistics."""
    logger.info("Fetching statistics for MAL ID %d...", mal_id)
    data = _fetch_json(f"{JIKAN_BASE}/anime/{mal_id}/statistics")
    if not data or "data" not in data:
        return {}

    stats = data["data"]
    result = {
        "watching": stats.get("watching", 0),
        "completed": stats.get("completed", 0),
        "on_hold": stats.get("on_hold", 0),
        "dropped": stats.get("dropped", 0),
        "plan_to_watch": stats.get("plan_to_watch", 0),
        "total": stats.get("total", 0),
        "scores": [],
    }
    for s in stats.get("scores", []):
        result["scores"].append({
            "score": s.get("score"),
            "votes": s.get("votes", 0),
            "percentage": s.get("percentage", 0),
        })

    logger.info("  -> Total users: %d, Completed: %d", result["total"], result["completed"])
    return result


def crawl_recommendations(mal_id: int = 516) -> list[dict]:
    """Fetch anime recommendations related to Keroro."""
    logger.info("Fetching recommendations for MAL ID %d...", mal_id)
    data = _fetch_json(f"{JIKAN_BASE}/anime/{mal_id}/recommendations")
    if not data or "data" not in data:
        return []

    results = []
    for rec in data["data"][:20]:
        entry = rec.get("entry", {})
        results.append({
            "mal_id": entry.get("mal_id"),
            "title": entry.get("title", ""),
            "image_url": entry.get("images", {}).get("jpg", {}).get("image_url", ""),
            "votes": rec.get("votes", 0),
        })

    results.sort(key=lambda x: x["votes"], reverse=True)
    logger.info("  -> Found %d recommendations", len(results))
    return results


def save_crawled_data(filename: str, data):
    """Save crawled data to JSON file."""
    os.makedirs(CRAWLED_DIR, exist_ok=True)
    filepath = os.path.join(CRAWLED_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved %s (%d bytes)", filepath, os.path.getsize(filepath))


def load_crawled_data(filename: str):
    """Load previously crawled data."""
    filepath = os.path.join(CRAWLED_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    return None


def import_to_db():
    """Import crawled JSON data into SQLite database."""
    db_path = os.path.join(BASE_DIR, "keroro.db")
    if not os.path.exists(db_path):
        logger.error("Database not found at %s. Run the server first to create it.", db_path)
        return

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    cursor = conn.cursor()

    # Create MAL tables if they don't exist
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS mal_anime (
            mal_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            title_english TEXT,
            title_japanese TEXT,
            type TEXT,
            episodes INTEGER,
            status TEXT,
            score REAL,
            scored_by INTEGER,
            rank INTEGER,
            popularity INTEGER,
            members INTEGER,
            favorites INTEGER,
            synopsis TEXT,
            season TEXT,
            year INTEGER,
            rating TEXT,
            duration TEXT,
            aired_from TEXT,
            aired_to TEXT,
            studios TEXT,
            genres TEXT,
            themes TEXT,
            demographics TEXT,
            image_url TEXT,
            key TEXT,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS mal_characters (
            mal_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            image_url TEXT,
            favorites INTEGER DEFAULT 0,
            role TEXT,
            voice_actors_json TEXT,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS mal_episodes (
            mal_id INTEGER PRIMARY KEY,
            title TEXT,
            title_japanese TEXT,
            title_romanji TEXT,
            aired TEXT,
            score REAL,
            filler INTEGER DEFAULT 0,
            recap INTEGER DEFAULT 0,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS mal_reviews (
            mal_id INTEGER PRIMARY KEY,
            username TEXT,
            score INTEGER,
            date TEXT,
            review TEXT,
            tags TEXT,
            episodes_watched INTEGER,
            is_spoiler INTEGER DEFAULT 0,
            is_preliminary INTEGER DEFAULT 0,
            reactions_json TEXT,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS mal_statistics (
            id INTEGER PRIMARY KEY DEFAULT 1,
            watching INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            on_hold INTEGER DEFAULT 0,
            dropped INTEGER DEFAULT 0,
            plan_to_watch INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            scores_json TEXT,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS mal_recommendations (
            mal_id INTEGER PRIMARY KEY,
            title TEXT,
            image_url TEXT,
            votes INTEGER DEFAULT 0,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_mal_chars_favorites ON mal_characters(favorites DESC);
        CREATE INDEX IF NOT EXISTS idx_mal_episodes_score ON mal_episodes(score DESC);
        CREATE INDEX IF NOT EXISTS idx_mal_reviews_score ON mal_reviews(score DESC);
        CREATE INDEX IF NOT EXISTS idx_mal_recs_votes ON mal_recommendations(votes DESC);
    """)
    conn.commit()

    # Import anime details
    anime_data = load_crawled_data("anime_details.json")
    if anime_data:
        for a in anime_data:
            cursor.execute("""
                INSERT OR REPLACE INTO mal_anime
                (mal_id, title, title_english, title_japanese, type, episodes, status,
                 score, scored_by, rank, popularity, members, favorites, synopsis,
                 season, year, rating, duration, aired_from, aired_to, studios,
                 genres, themes, demographics, image_url, key)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                a["mal_id"], a["title"], a["title_english"], a["title_japanese"],
                a["type"], a["episodes"], a["status"], a["score"], a["scored_by"],
                a["rank"], a["popularity"], a["members"], a["favorites"],
                a["synopsis"], a["season"], a["year"], a["rating"], a["duration"],
                a["aired_from"], a["aired_to"], a["studios"], a["genres"],
                a["themes"], a["demographics"], a["image_url"], a["key"],
            ))
        conn.commit()
        logger.info("Imported %d anime entries", len(anime_data))

    # Import characters
    chars_data = load_crawled_data("mal_characters.json")
    if chars_data:
        for c in chars_data:
            cursor.execute("""
                INSERT OR REPLACE INTO mal_characters
                (mal_id, name, image_url, favorites, role, voice_actors_json)
                VALUES (?,?,?,?,?,?)
            """, (
                c["mal_id"], c["name"], c["image_url"], c["favorites"],
                c["role"], json.dumps(c.get("voice_actors", []), ensure_ascii=False),
            ))
        conn.commit()
        logger.info("Imported %d MAL characters", len(chars_data))

    # Import episodes
    eps_data = load_crawled_data("mal_episodes.json")
    if eps_data:
        for ep in eps_data:
            cursor.execute("""
                INSERT OR REPLACE INTO mal_episodes
                (mal_id, title, title_japanese, title_romanji, aired, score, filler, recap)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                ep["mal_id"], ep["title"], ep["title_japanese"],
                ep.get("title_romanji", ""), ep["aired"], ep["score"],
                1 if ep.get("filler") else 0, 1 if ep.get("recap") else 0,
            ))
        conn.commit()
        logger.info("Imported %d MAL episodes", len(eps_data))

    # Import reviews
    reviews_data = load_crawled_data("mal_reviews.json")
    if reviews_data:
        for r in reviews_data:
            cursor.execute("""
                INSERT OR REPLACE INTO mal_reviews
                (mal_id, username, score, date, review, tags, episodes_watched,
                 is_spoiler, is_preliminary, reactions_json)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                r["mal_id"], r["username"], r["score"], r["date"],
                r["review"], json.dumps(r.get("tags", [])),
                r.get("episodes_watched"), 1 if r.get("is_spoiler") else 0,
                1 if r.get("is_preliminary") else 0,
                json.dumps(r.get("reactions", {})),
            ))
        conn.commit()
        logger.info("Imported %d MAL reviews", len(reviews_data))

    # Import statistics
    stats_data = load_crawled_data("mal_statistics.json")
    if stats_data:
        cursor.execute("""
            INSERT OR REPLACE INTO mal_statistics
            (id, watching, completed, on_hold, dropped, plan_to_watch, total, scores_json)
            VALUES (1,?,?,?,?,?,?,?)
        """, (
            stats_data.get("watching", 0), stats_data.get("completed", 0),
            stats_data.get("on_hold", 0), stats_data.get("dropped", 0),
            stats_data.get("plan_to_watch", 0), stats_data.get("total", 0),
            json.dumps(stats_data.get("scores", []), ensure_ascii=False),
        ))
        conn.commit()
        logger.info("Imported MAL statistics")

    # Import recommendations
    recs_data = load_crawled_data("mal_recommendations.json")
    if recs_data:
        for rec in recs_data:
            cursor.execute("""
                INSERT OR REPLACE INTO mal_recommendations
                (mal_id, title, image_url, votes)
                VALUES (?,?,?,?)
            """, (rec["mal_id"], rec["title"], rec["image_url"], rec["votes"]))
        conn.commit()
        logger.info("Imported %d MAL recommendations", len(recs_data))

    conn.close()
    logger.info("Database import complete!")


def run_full_crawl():
    """Run complete crawl of all data."""
    logger.info("=" * 60)
    logger.info("Starting full Keroro Gunso MAL crawl...")
    logger.info("=" * 60)

    # 1. Anime details for all entries
    anime = crawl_anime_details()
    save_crawled_data("anime_details.json", anime)

    # 2. Characters (main TV series)
    characters = crawl_characters(MAL_IDS["tv"])
    save_crawled_data("mal_characters.json", characters)

    # 3. Episodes (main TV series - 358 eps, ~15 pages)
    episodes = crawl_episodes(MAL_IDS["tv"])
    save_crawled_data("mal_episodes.json", episodes)

    # 4. Reviews
    reviews = crawl_reviews(MAL_IDS["tv"], pages=5)
    save_crawled_data("mal_reviews.json", reviews)

    # 5. Statistics
    statistics = crawl_statistics(MAL_IDS["tv"])
    save_crawled_data("mal_statistics.json", statistics)

    # 6. Recommendations
    recommendations = crawl_recommendations(MAL_IDS["tv"])
    save_crawled_data("mal_recommendations.json", recommendations)

    logger.info("=" * 60)
    logger.info("Crawl complete! Importing to database...")
    logger.info("=" * 60)

    # Import all to DB
    import_to_db()

    logger.info("=" * 60)
    logger.info("All done! Data saved to %s and imported to DB.", CRAWLED_DIR)
    logger.info("=" * 60)


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--import-only" in args:
        import_to_db()
    elif "--characters" in args:
        chars = crawl_characters(MAL_IDS["tv"])
        save_crawled_data("mal_characters.json", chars)
    elif "--episodes" in args:
        eps = crawl_episodes(MAL_IDS["tv"])
        save_crawled_data("mal_episodes.json", eps)
    elif "--reviews" in args:
        revs = crawl_reviews(MAL_IDS["tv"])
        save_crawled_data("mal_reviews.json", revs)
    elif "--stats" in args:
        stats = crawl_statistics(MAL_IDS["tv"])
        save_crawled_data("mal_statistics.json", stats)
    else:
        run_full_crawl()
