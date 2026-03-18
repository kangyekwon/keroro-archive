"""
AniList GraphQL API Crawler for Keroro Gunso Archive.

Fetches data from AniList to compare with MAL data:
- Anime details (score, popularity, trending, tags)
- Character popularity on AniList
- Studio information
- User statistics

Usage:
    python -m crawler.anilist_crawler
"""

import json
import logging
import os
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CRAWLED_DIR = os.path.join(DATA_DIR, "crawled")

ANILIST_URL = "https://graphql.anilist.co"
RATE_LIMIT = 1.5


def _graphql_query(query: str, variables: dict = None, retries: int = 3) -> dict | None:
    """Execute AniList GraphQL query."""
    payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")

    for attempt in range(retries):
        try:
            time.sleep(RATE_LIMIT)
            req = Request(
                ANILIST_URL,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "KeroroArchive/1.0",
                },
                method="POST",
            )
            with urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except HTTPError as e:
            if e.code == 429:
                wait = 5 * (attempt + 1)
                logger.warning("AniList rate limited (429). Waiting %ds...", wait)
                time.sleep(wait)
            else:
                logger.error("HTTP %d from AniList", e.code)
                time.sleep(2)
        except (URLError, TimeoutError) as e:
            logger.warning("Connection error (attempt %d/%d): %s", attempt + 1, retries, e)
            time.sleep(3)
        except json.JSONDecodeError as e:
            logger.error("JSON decode error: %s", e)
            return None
    return None


def crawl_anilist_anime() -> dict | None:
    """Fetch Keroro Gunso anime data from AniList."""
    logger.info("Fetching Keroro anime from AniList...")

    query = """
    query ($search: String) {
        Media(search: $search, type: ANIME) {
            id
            idMal
            title {
                romaji
                english
                native
            }
            format
            episodes
            duration
            status
            startDate { year month day }
            endDate { year month day }
            season
            seasonYear
            averageScore
            meanScore
            popularity
            trending
            favourites
            genres
            tags {
                name
                rank
                category
            }
            studios {
                nodes {
                    id
                    name
                    isAnimationStudio
                }
            }
            staff(sort: RELEVANCE, perPage: 25) {
                nodes {
                    id
                    name { full native }
                    primaryOccupations
                }
            }
            stats {
                scoreDistribution {
                    score
                    amount
                }
                statusDistribution {
                    status
                    amount
                }
            }
            rankings {
                id
                rank
                type
                format
                year
                season
                allTime
                context
            }
            recommendations(sort: RATING_DESC, perPage: 10) {
                nodes {
                    mediaRecommendation {
                        id
                        title { romaji english }
                        averageScore
                        coverImage { large }
                    }
                    rating
                }
            }
            relations {
                edges {
                    relationType
                    node {
                        id
                        idMal
                        title { romaji english native }
                        type
                        format
                        status
                        averageScore
                        coverImage { large }
                    }
                }
            }
            coverImage { large extraLarge }
            bannerImage
            siteUrl
        }
    }
    """

    data = _graphql_query(query, {"search": "Keroro Gunsou"})
    if not data or "data" not in data or not data["data"].get("Media"):
        logger.error("Failed to fetch Keroro from AniList")
        return None

    media = data["data"]["Media"]
    logger.info("  -> Found: %s (AniList ID: %d, MAL ID: %s)",
                media["title"]["romaji"], media["id"], media.get("idMal"))
    logger.info("  -> Score: %s, Popularity: %s, Favourites: %s",
                media.get("averageScore"), media.get("popularity"), media.get("favourites"))

    return media


def crawl_anilist_characters() -> list[dict]:
    """Fetch character popularity data from AniList."""
    logger.info("Fetching Keroro characters from AniList...")

    query = """
    query ($search: String, $page: Int) {
        Media(search: $search, type: ANIME) {
            characters(sort: FAVOURITES_DESC, page: $page, perPage: 25) {
                pageInfo { hasNextPage currentPage }
                edges {
                    role
                    node {
                        id
                        name { full native }
                        image { large }
                        favourites
                        siteUrl
                    }
                    voiceActors(language: JAPANESE) {
                        id
                        name { full native }
                        image { large }
                    }
                }
            }
        }
    }
    """

    all_chars = []
    page = 1
    has_next = True

    while has_next and page <= 4:
        data = _graphql_query(query, {"search": "Keroro Gunsou", "page": page})
        if not data or "data" not in data:
            break

        media = data["data"].get("Media")
        if not media:
            break

        chars = media.get("characters", {})
        edges = chars.get("edges", [])
        if not edges:
            break

        for edge in edges:
            node = edge.get("node", {})
            vas = edge.get("voiceActors", [])
            all_chars.append({
                "anilist_id": node.get("id"),
                "name": node.get("name", {}).get("full", ""),
                "name_native": node.get("name", {}).get("native", ""),
                "image_url": node.get("image", {}).get("large", ""),
                "favourites": node.get("favourites", 0),
                "role": edge.get("role", ""),
                "voice_actors": [
                    {
                        "id": va.get("id"),
                        "name": va.get("name", {}).get("full", ""),
                        "name_native": va.get("name", {}).get("native", ""),
                    }
                    for va in vas[:2]
                ],
            })

        has_next = chars.get("pageInfo", {}).get("hasNextPage", False)
        page += 1
        logger.info("  -> Page %d: %d characters (total: %d)", page - 1, len(edges), len(all_chars))

    all_chars.sort(key=lambda x: x["favourites"], reverse=True)
    logger.info("  -> Total AniList characters: %d", len(all_chars))
    return all_chars


def save_crawled_data(filename: str, data):
    """Save crawled data to JSON file."""
    os.makedirs(CRAWLED_DIR, exist_ok=True)
    filepath = os.path.join(CRAWLED_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved %s (%d bytes)", filepath, os.path.getsize(filepath))


def run_anilist_crawl():
    """Run complete AniList crawl."""
    logger.info("=" * 60)
    logger.info("Starting AniList crawl for Keroro Gunso...")
    logger.info("=" * 60)

    # 1. Main anime data
    anime = crawl_anilist_anime()
    if anime:
        save_crawled_data("anilist_anime.json", anime)

    # 2. Character data
    characters = crawl_anilist_characters()
    if characters:
        save_crawled_data("anilist_characters.json", characters)

    logger.info("=" * 60)
    logger.info("AniList crawl complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_anilist_crawl()
