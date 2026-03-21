"""FastAPI backend server for Keroro Archive"""

import json
import logging
import math
import os
import random
import sys
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import APP_NAME, CORS_ORIGINS

from db import Database
from search import SearchEngine

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")
DATA_DIR = os.path.join(BASE_DIR, "data")

_db: Database | None = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db


# === Rate Limiter ===


class SimpleRateLimiter:
    """In-memory rate limiter for abuse prevention."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        self.requests[key] = [t for t in self.requests[key] if now - t < self.window]
        if len(self.requests[key]) >= self.max_requests:
            return False
        self.requests[key].append(now)
        return True


post_limiter = SimpleRateLimiter(max_requests=10, window_seconds=60)
visitor_limiter = SimpleRateLimiter(max_requests=30, window_seconds=60)


def get_client_ip(request: Request) -> str:
    """Extract client IP for rate limiting."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# === Security Headers Middleware ===


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all HTTP responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # No-cache for static files to prevent stale JS/CSS
        req_path = request.url.path
        if req_path.startswith("/static/") or req_path.endswith((".js", ".css")):
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        return response


# === Pydantic Models ===


class GuestbookEntry(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=20)
    message: str = Field(..., min_length=1, max_length=300)
    keroro_pick: str = Field(default="", max_length=50)


class BoardEntry(BaseModel):
    author: str = Field(..., min_length=1, max_length=30)
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=2000)
    category: str = Field(default="general", max_length=30)


class VoteEntry(BaseModel):
    character_id: int = Field(..., gt=0)
    voter_nickname: str = Field(default="anonymous", max_length=20)


# === JSON Data Loading ===


def _load_json_file(filename: str, default=None):
    """Load a JSON file from the data directory."""
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else []


def _seed_db_from_json():
    """Seed SQLite DB from data/*.json files if tables are empty."""
    db = get_db()

    # Seed characters
    count = db.fetchone("SELECT COUNT(*) as cnt FROM characters")
    if count and count["cnt"] == 0:
        characters = _load_json_file("characters.json", [])
        if characters:
            params_list = []
            for c in characters:
                params_list.append((
                    c.get("name", ""),
                    c.get("name_kr", ""),
                    c.get("race", "Keronian"),
                    c.get("platoon", ""),
                    c.get("rank", ""),
                    c.get("color", ""),
                    c.get("ability", ""),
                    c.get("personality", ""),
                    c.get("description", ""),
                    c.get("image_url", ""),
                    c.get("first_appearance"),
                ))
            try:
                db.executemany(
                    "INSERT OR IGNORE INTO characters "
                    "(name, name_kr, race, platoon, rank, color, ability, personality, description, image_url, first_appearance) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    params_list,
                )
                logger.info("Seeded %d characters", len(params_list))
            except Exception as e:
                logger.warning("Failed to seed characters: %s", e)

    # Seed episodes
    count = db.fetchone("SELECT COUNT(*) as cnt FROM episodes")
    if count and count["cnt"] == 0:
        episodes = _load_json_file("episodes.json", [])
        if episodes:
            params_list = []
            for ep in episodes:
                params_list.append((
                    ep.get("episode_no", 0),
                    ep.get("title", ""),
                    ep.get("title_kr", ""),
                    ep.get("air_date", ""),
                    ep.get("season", 1),
                    ep.get("arc", ""),
                    ep.get("summary", ""),
                ))
            try:
                db.executemany(
                    "INSERT OR IGNORE INTO episodes "
                    "(episode_no, title, title_kr, air_date, season, arc, summary) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    params_list,
                )
                logger.info("Seeded %d episodes", len(params_list))
            except Exception as e:
                logger.warning("Failed to seed episodes: %s", e)

    # Seed quotes
    count = db.fetchone("SELECT COUNT(*) as cnt FROM quotes")
    if count and count["cnt"] == 0:
        quotes = _load_json_file("quotes.json", [])
        if quotes:
            params_list = []
            for q in quotes:
                params_list.append((
                    q.get("character_id", 1),
                    q.get("content", ""),
                    q.get("content_kr", ""),
                    q.get("episode_id"),
                    q.get("context", ""),
                ))
            try:
                db.executemany(
                    "INSERT OR IGNORE INTO quotes "
                    "(character_id, content, content_kr, episode_id, context) "
                    "VALUES (?, ?, ?, ?, ?)",
                    params_list,
                )
                logger.info("Seeded %d quotes", len(params_list))
            except Exception as e:
                logger.warning("Failed to seed quotes: %s", e)

    # Seed items
    count = db.fetchone("SELECT COUNT(*) as cnt FROM items")
    if count and count["cnt"] == 0:
        items = _load_json_file("items.json", [])
        if items:
            params_list = []
            for it in items:
                params_list.append((
                    it.get("name", ""),
                    it.get("name_kr", ""),
                    it.get("category", "other"),
                    it.get("owner", ""),
                    it.get("description", ""),
                    it.get("image_url", ""),
                ))
            try:
                db.executemany(
                    "INSERT OR IGNORE INTO items "
                    "(name, name_kr, category, owner, description, image_url) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    params_list,
                )
                logger.info("Seeded %d items", len(params_list))
            except Exception as e:
                logger.warning("Failed to seed items: %s", e)

    # Seed character relations
    count = db.fetchone("SELECT COUNT(*) as cnt FROM character_relations")
    if count and count["cnt"] == 0:
        relations = _load_json_file("relations.json", [])
        if relations:
            params_list = []
            for r in relations:
                params_list.append((
                    r.get("char_from", 0),
                    r.get("char_to", 0),
                    r.get("relation_type", "friend"),
                    r.get("description", ""),
                ))
            try:
                db.executemany(
                    "INSERT OR IGNORE INTO character_relations "
                    "(char_from, char_to, relation_type, description) "
                    "VALUES (?, ?, ?, ?)",
                    params_list,
                )
                logger.info("Seeded %d relations", len(params_list))
            except Exception as e:
                logger.warning("Failed to seed relations: %s", e)

    # Seed invasion plans
    count = db.fetchone("SELECT COUNT(*) as cnt FROM invasion_plans")
    if count and count["cnt"] == 0:
        plans = _load_json_file("invasion_plans.json", [])
        if plans:
            params_list = []
            for p in plans:
                params_list.append((
                    p.get("name", ""),
                    p.get("name_kr", ""),
                    p.get("planner_id"),
                    p.get("episode_id"),
                    p.get("method", ""),
                    p.get("result", ""),
                    p.get("result_reason", ""),
                    p.get("description", ""),
                ))
            try:
                db.executemany(
                    "INSERT OR IGNORE INTO invasion_plans "
                    "(name, name_kr, planner_id, episode_id, method, result, result_reason, description) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    params_list,
                )
                logger.info("Seeded %d invasion plans", len(params_list))
            except Exception as e:
                logger.warning("Failed to seed invasion plans: %s", e)

    # Seed abilities
    count = db.fetchone("SELECT COUNT(*) as cnt FROM abilities")
    if count and count["cnt"] == 0:
        abilities = _load_json_file("abilities.json", [])
        if abilities:
            params_list = []
            for a in abilities:
                params_list.append((
                    a.get("name", ""),
                    a.get("name_kr", ""),
                    a.get("character_id"),
                    a.get("type", ""),
                    a.get("power_level", 0),
                    a.get("description", ""),
                    a.get("first_used_episode"),
                ))
            try:
                db.executemany(
                    "INSERT OR IGNORE INTO abilities "
                    "(name, name_kr, character_id, type, power_level, description, first_used_episode) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    params_list,
                )
                logger.info("Seeded %d abilities", len(params_list))
            except Exception as e:
                logger.warning("Failed to seed abilities: %s", e)

    # Seed OST
    count = db.fetchone("SELECT COUNT(*) as cnt FROM ost")
    if count and count["cnt"] == 0:
        ost_list = _load_json_file("ost.json", [])
        if ost_list:
            params_list = []
            for o in ost_list:
                params_list.append((
                    o.get("title", ""),
                    o.get("title_kr", ""),
                    o.get("artist", ""),
                    o.get("type", ""),
                    o.get("season"),
                    o.get("episode_start"),
                    o.get("episode_end"),
                    o.get("release_date", ""),
                    o.get("description", ""),
                ))
            try:
                db.executemany(
                    "INSERT OR IGNORE INTO ost "
                    "(title, title_kr, artist, type, season, episode_start, episode_end, release_date, description) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    params_list,
                )
                logger.info("Seeded %d OST entries", len(params_list))
            except Exception as e:
                logger.warning("Failed to seed OST: %s", e)

    # Seed voice actors
    count = db.fetchone("SELECT COUNT(*) as cnt FROM voice_actors")
    if count and count["cnt"] == 0:
        actors = _load_json_file("voice_actors.json", [])
        if actors:
            params_list = []
            for va in actors:
                params_list.append((
                    va.get("character_id"),
                    va.get("actor_name", ""),
                    va.get("actor_name_kr", ""),
                    va.get("language", ""),
                    va.get("other_roles", ""),
                ))
            try:
                db.executemany(
                    "INSERT OR IGNORE INTO voice_actors "
                    "(character_id, actor_name, actor_name_kr, language, other_roles) "
                    "VALUES (?, ?, ?, ?, ?)",
                    params_list,
                )
                logger.info("Seeded %d voice actors", len(params_list))
            except Exception as e:
                logger.warning("Failed to seed voice actors: %s", e)

    # Seed military ranks
    count = db.fetchone("SELECT COUNT(*) as cnt FROM military_ranks")
    if count and count["cnt"] == 0:
        ranks = _load_json_file("military_ranks.json", [])
        if ranks:
            params_list = []
            for rk in ranks:
                params_list.append((
                    rk.get("rank_name", ""),
                    rk.get("rank_name_kr", ""),
                    rk.get("rank_level", 0),
                    rk.get("description", ""),
                    rk.get("notable_holders", ""),
                ))
            try:
                db.executemany(
                    "INSERT OR IGNORE INTO military_ranks "
                    "(rank_name, rank_name_kr, rank_level, description, notable_holders) "
                    "VALUES (?, ?, ?, ?, ?)",
                    params_list,
                )
                logger.info("Seeded %d military ranks", len(params_list))
            except Exception as e:
                logger.warning("Failed to seed military ranks: %s", e)


# === Lifespan ===


def _create_mal_tables():
    """Create MAL analytics tables if they don't exist."""
    db = get_db()
    try:
        db.execute("""
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
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS mal_characters (
                mal_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                image_url TEXT,
                favorites INTEGER DEFAULT 0,
                role TEXT,
                voice_actors_json TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
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
            )
        """)
        db.execute("""
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
            )
        """)
        db.execute("""
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
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS mal_recommendations (
                mal_id INTEGER PRIMARY KEY,
                title TEXT,
                image_url TEXT,
                votes INTEGER DEFAULT 0,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Extended MAL tables
        db.execute("""
            CREATE TABLE IF NOT EXISTS mal_staff (
                mal_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                image_url TEXT,
                positions_json TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS mal_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mal_id INTEGER,
                type TEXT,
                name TEXT,
                url TEXT,
                relation TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS mal_manga (
                mal_id INTEGER PRIMARY KEY,
                title TEXT,
                title_english TEXT,
                title_japanese TEXT,
                type TEXT,
                chapters INTEGER,
                volumes INTEGER,
                status TEXT,
                score REAL,
                scored_by INTEGER,
                rank INTEGER,
                popularity INTEGER,
                members INTEGER,
                favorites INTEGER,
                synopsis TEXT,
                published_from TEXT,
                published_to TEXT,
                authors TEXT,
                serializations TEXT,
                genres TEXT,
                image_url TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS mal_manga_characters (
                mal_id INTEGER PRIMARY KEY,
                name TEXT,
                image_url TEXT,
                role TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS anilist_anime (
                anilist_id INTEGER PRIMARY KEY,
                id_mal INTEGER,
                title_romaji TEXT,
                title_english TEXT,
                title_native TEXT,
                format TEXT,
                episodes INTEGER,
                average_score INTEGER,
                mean_score INTEGER,
                popularity INTEGER,
                trending INTEGER,
                favourites INTEGER,
                genres_json TEXT,
                tags_json TEXT,
                studios_json TEXT,
                stats_json TEXT,
                rankings_json TEXT,
                relations_json TEXT,
                recommendations_json TEXT,
                cover_image TEXT,
                banner_image TEXT,
                site_url TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS anilist_characters (
                anilist_id INTEGER PRIMARY KEY,
                name TEXT,
                name_native TEXT,
                image_url TEXT,
                favourites INTEGER DEFAULT 0,
                role TEXT,
                voice_actors_json TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("MAL analytics tables ready (including extended)")
    except Exception as e:
        logger.warning("Failed to create MAL tables: %s", e)


def _seed_mal_from_crawled():
    """Import crawled MAL data from JSON files if tables are empty."""
    db = get_db()
    crawled_dir = os.path.join(DATA_DIR, "crawled")
    if not os.path.exists(crawled_dir):
        return

    def _load_crawled(filename):
        fp = os.path.join(crawled_dir, filename)
        if os.path.exists(fp):
            with open(fp, encoding="utf-8") as f:
                return json.load(f)
        return None

    # Anime details
    count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_anime")
    if count and count["cnt"] == 0:
        data = _load_crawled("anime_details.json")
        if data:
            for a in data:
                try:
                    db.execute(
                        "INSERT OR IGNORE INTO mal_anime "
                        "(mal_id,title,title_english,title_japanese,type,episodes,status,"
                        "score,scored_by,rank,popularity,members,favorites,synopsis,"
                        "season,year,rating,duration,aired_from,aired_to,studios,"
                        "genres,themes,demographics,image_url,key) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (a.get("mal_id"), a.get("title",""), a.get("title_english",""),
                         a.get("title_japanese",""), a.get("type",""), a.get("episodes"),
                         a.get("status",""), a.get("score"), a.get("scored_by"),
                         a.get("rank"), a.get("popularity"), a.get("members"),
                         a.get("favorites"), a.get("synopsis",""), a.get("season",""),
                         a.get("year"), a.get("rating",""), a.get("duration",""),
                         a.get("aired_from",""), a.get("aired_to",""), a.get("studios",""),
                         a.get("genres",""), a.get("themes",""), a.get("demographics",""),
                         a.get("image_url",""), a.get("key","")),
                    )
                except Exception as e:
                    logger.warning("Failed to insert anime %s: %s", a.get("mal_id"), e)
            logger.info("Seeded %d MAL anime entries", len(data))

    # Characters
    count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_characters")
    if count and count["cnt"] == 0:
        data = _load_crawled("mal_characters.json")
        if data:
            for c in data:
                try:
                    db.execute(
                        "INSERT OR IGNORE INTO mal_characters "
                        "(mal_id,name,image_url,favorites,role,voice_actors_json) "
                        "VALUES (?,?,?,?,?,?)",
                        (c.get("mal_id"), c.get("name",""), c.get("image_url",""),
                         c.get("favorites",0), c.get("role",""),
                         json.dumps(c.get("voice_actors",[]), ensure_ascii=False)),
                    )
                except Exception as e:
                    logger.warning("Failed to insert character %s: %s", c.get("mal_id"), e)
            logger.info("Seeded %d MAL characters", len(data))

    # Episodes
    count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_episodes")
    if count and count["cnt"] == 0:
        data = _load_crawled("mal_episodes.json")
        if data:
            for ep in data:
                try:
                    db.execute(
                        "INSERT OR IGNORE INTO mal_episodes "
                        "(mal_id,title,title_japanese,title_romanji,aired,score,filler,recap) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (ep.get("mal_id"), ep.get("title",""), ep.get("title_japanese",""),
                         ep.get("title_romanji",""), ep.get("aired",""), ep.get("score"),
                         1 if ep.get("filler") else 0, 1 if ep.get("recap") else 0),
                    )
                except Exception as e:
                    logger.warning("Failed to insert episode %s: %s", ep.get("mal_id"), e)
            logger.info("Seeded %d MAL episodes", len(data))

    # Reviews
    count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_reviews")
    if count and count["cnt"] == 0:
        data = _load_crawled("mal_reviews.json")
        if data:
            for r in data:
                try:
                    db.execute(
                        "INSERT OR IGNORE INTO mal_reviews "
                        "(mal_id,username,score,date,review,tags,episodes_watched,"
                        "is_spoiler,is_preliminary,reactions_json) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (r.get("mal_id"), r.get("username",""), r.get("score"),
                         r.get("date",""), r.get("review",""),
                         json.dumps(r.get("tags",[]), ensure_ascii=False),
                         r.get("episodes_watched"),
                         1 if r.get("is_spoiler") else 0,
                         1 if r.get("is_preliminary") else 0,
                         json.dumps(r.get("reactions",{}), ensure_ascii=False)),
                    )
                except Exception as e:
                    logger.warning("Failed to insert review %s: %s", r.get("mal_id"), e)
            logger.info("Seeded %d MAL reviews", len(data))

    # Statistics
    count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_statistics")
    if count and count["cnt"] == 0:
        data = _load_crawled("mal_statistics.json")
        if data:
            try:
                db.execute(
                    "INSERT OR IGNORE INTO mal_statistics "
                    "(id,watching,completed,on_hold,dropped,plan_to_watch,total,scores_json) "
                    "VALUES (1,?,?,?,?,?,?,?)",
                    (data.get("watching",0), data.get("completed",0), data.get("on_hold",0),
                     data.get("dropped",0), data.get("plan_to_watch",0), data.get("total",0),
                     json.dumps(data.get("scores",[]), ensure_ascii=False)),
                )
                logger.info("Seeded MAL statistics")
            except Exception as e:
                logger.warning("Failed to insert statistics: %s", e)

    # Recommendations
    count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_recommendations")
    if count and count["cnt"] == 0:
        data = _load_crawled("mal_recommendations.json")
        if data:
            for rec in data:
                try:
                    db.execute(
                        "INSERT OR IGNORE INTO mal_recommendations "
                        "(mal_id,title,image_url,votes) VALUES (?,?,?,?)",
                        (rec.get("mal_id"), rec.get("title",""),
                         rec.get("image_url",""), rec.get("votes",0)),
                    )
                except Exception as e:
                    logger.warning("Failed to insert recommendation %s: %s", rec.get("mal_id"), e)
            logger.info("Seeded %d MAL recommendations", len(data))

    # Staff
    count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_staff")
    if count and count["cnt"] == 0:
        data = _load_crawled("mal_staff.json")
        if data:
            for s in data:
                try:
                    db.execute(
                        "INSERT OR IGNORE INTO mal_staff (mal_id,name,image_url,positions_json) VALUES (?,?,?,?)",
                        (s.get("mal_id"), s.get("name",""), s.get("image_url",""),
                         json.dumps(s.get("positions",[]), ensure_ascii=False)),
                    )
                except Exception as e:
                    logger.warning("Failed to insert staff %s: %s", s.get("mal_id"), e)
            logger.info("Seeded %d MAL staff", len(data))

    # Relations
    count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_relations")
    if count and count["cnt"] == 0:
        data = _load_crawled("mal_relations.json")
        if data:
            for r in data:
                try:
                    db.execute(
                        "INSERT INTO mal_relations (mal_id,type,name,url,relation) VALUES (?,?,?,?,?)",
                        (r.get("mal_id"), r.get("type",""), r.get("name",""),
                         r.get("url",""), r.get("relation","")),
                    )
                except Exception as e:
                    logger.warning("Failed to insert relation: %s", e)
            logger.info("Seeded %d MAL relations", len(data))

    # Manga
    count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_manga")
    if count and count["cnt"] == 0:
        data = _load_crawled("mal_manga.json")
        if data and isinstance(data, dict):
            try:
                db.execute(
                    "INSERT OR IGNORE INTO mal_manga "
                    "(mal_id,title,title_english,title_japanese,type,chapters,volumes,"
                    "status,score,scored_by,rank,popularity,members,favorites,"
                    "synopsis,published_from,published_to,authors,serializations,genres,image_url) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (data.get("mal_id"), data.get("title",""), data.get("title_english",""),
                     data.get("title_japanese",""), data.get("type",""), data.get("chapters"),
                     data.get("volumes"), data.get("status",""), data.get("score"),
                     data.get("scored_by"), data.get("rank"), data.get("popularity"),
                     data.get("members"), data.get("favorites"), data.get("synopsis",""),
                     data.get("published_from",""), data.get("published_to",""),
                     data.get("authors",""), data.get("serializations",""),
                     data.get("genres",""), data.get("image_url","")),
                )
                logger.info("Seeded MAL manga data")
            except Exception as e:
                logger.warning("Failed to insert manga: %s", e)

    # Manga characters
    count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_manga_characters")
    if count and count["cnt"] == 0:
        data = _load_crawled("mal_manga_characters.json")
        if data:
            for mc in data:
                try:
                    db.execute(
                        "INSERT OR IGNORE INTO mal_manga_characters (mal_id,name,image_url,role) VALUES (?,?,?,?)",
                        (mc.get("mal_id"), mc.get("name",""), mc.get("image_url",""), mc.get("role","")),
                    )
                except Exception as e:
                    logger.warning("Failed to insert manga character: %s", e)
            logger.info("Seeded %d manga characters", len(data))

    # AniList anime
    count = db.fetchone("SELECT COUNT(*) as cnt FROM anilist_anime")
    if count and count["cnt"] == 0:
        data = _load_crawled("anilist_anime.json")
        if data and isinstance(data, dict):
            try:
                db.execute(
                    "INSERT OR IGNORE INTO anilist_anime "
                    "(anilist_id,id_mal,title_romaji,title_english,title_native,format,"
                    "episodes,average_score,mean_score,popularity,trending,favourites,"
                    "genres_json,tags_json,studios_json,stats_json,rankings_json,"
                    "relations_json,recommendations_json,cover_image,banner_image,site_url) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (data.get("id"), data.get("idMal"),
                     data.get("title",{}).get("romaji",""),
                     data.get("title",{}).get("english",""),
                     data.get("title",{}).get("native",""),
                     data.get("format",""), data.get("episodes"),
                     data.get("averageScore"), data.get("meanScore"),
                     data.get("popularity"), data.get("trending"),
                     data.get("favourites"),
                     json.dumps(data.get("genres",[]), ensure_ascii=False),
                     json.dumps(data.get("tags",[]), ensure_ascii=False),
                     json.dumps(data.get("studios",{}).get("nodes",[]), ensure_ascii=False),
                     json.dumps(data.get("stats",{}), ensure_ascii=False),
                     json.dumps(data.get("rankings",[]), ensure_ascii=False),
                     json.dumps(data.get("relations",{}).get("edges",[]), ensure_ascii=False),
                     json.dumps(data.get("recommendations",{}).get("nodes",[]), ensure_ascii=False),
                     data.get("coverImage",{}).get("extraLarge",""),
                     data.get("bannerImage",""),
                     data.get("siteUrl","")),
                )
                logger.info("Seeded AniList anime data")
            except Exception as e:
                logger.warning("Failed to insert AniList anime: %s", e)

    # AniList characters
    count = db.fetchone("SELECT COUNT(*) as cnt FROM anilist_characters")
    if count and count["cnt"] == 0:
        data = _load_crawled("anilist_characters.json")
        if data:
            for c in data:
                try:
                    db.execute(
                        "INSERT OR IGNORE INTO anilist_characters "
                        "(anilist_id,name,name_native,image_url,favourites,role,voice_actors_json) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (c.get("anilist_id"), c.get("name",""), c.get("name_native",""),
                         c.get("image_url",""), c.get("favourites",0), c.get("role",""),
                         json.dumps(c.get("voice_actors",[]), ensure_ascii=False)),
                    )
                except Exception as e:
                    logger.warning("Failed to insert AniList character: %s", e)
            logger.info("Seeded %d AniList characters", len(data))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _db
    _db = Database()
    _seed_db_from_json()
    _create_mal_tables()
    _seed_mal_from_crawled()
    yield
    if _db is not None:
        _db.close()
        _db = None


# === App ===

app = FastAPI(title=f"{APP_NAME} API", lifespan=lifespan)

# Security headers (added first to wrap all responses)
app.add_middleware(SecurityHeadersMiddleware)

# CORS
_cors_origins = CORS_ORIGINS
if _cors_origins == ["*"]:
    logger.warning(
        "CORS is set to wildcard '*'. Set CORS_ORIGINS env var for production "
        "(e.g. CORS_ORIGINS=https://yourdomain.com)."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False if _cors_origins == ["*"] else True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Accept"],
)


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# === Static files ===

if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
    if os.path.exists(os.path.join(WEB_DIR, "css")):
        app.mount("/css", StaticFiles(directory=os.path.join(WEB_DIR, "css")), name="css")
    if os.path.exists(os.path.join(WEB_DIR, "js")):
        app.mount("/js", StaticFiles(directory=os.path.join(WEB_DIR, "js")), name="js")
    if os.path.exists(os.path.join(WEB_DIR, "images")):
        app.mount("/images", StaticFiles(directory=os.path.join(WEB_DIR, "images")), name="images")


# ============================================================
# Routes
# ============================================================


# === Index ===

@app.get("/")
def index():
    """Serve the web frontend."""
    index_path = os.path.join(WEB_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_path)


# === Search ===

@app.get("/api/search")
def search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Search across characters, episodes, quotes, and items."""
    db = get_db()
    engine = SearchEngine(db)
    return engine.search_all(q, limit=limit, offset=offset)


@app.get("/api/suggest")
def suggest(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
    """Auto-suggest character names."""
    db = get_db()
    engine = SearchEngine(db)
    return {"suggestions": engine.suggest(q, limit=limit)}


# === Characters ===

@app.get("/api/characters")
def characters_list(
    race: str = Query(None, description="Filter by race (e.g. Keronian, Human)"),
    platoon: str = Query(None, description="Filter by platoon"),
):
    """List all characters with optional filters."""
    db = get_db()
    where_clauses = []
    params: list = []
    if race:
        where_clauses.append("race = ?")
        params.append(race)
    if platoon:
        where_clauses.append("platoon = ?")
        params.append(platoon)

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    rows = db.fetchall(
        f"SELECT * FROM characters{where_sql} ORDER BY id",
        tuple(params),
    )
    return {"characters": [dict(r) for r in rows], "total": len(rows)}


@app.get("/api/characters/{character_id}")
def character_detail(character_id: int):
    """Get a single character with relations and quotes."""
    db = get_db()
    character = db.fetchone("SELECT * FROM characters WHERE id = ?", (character_id,))
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Relations where this character is involved
    relations_out = db.fetchall(
        "SELECT cr.*, c.name, c.name_kr, c.image_url "
        "FROM character_relations cr "
        "JOIN characters c ON cr.char_to = c.id "
        "WHERE cr.char_from = ?",
        (character_id,),
    )
    relations_in = db.fetchall(
        "SELECT cr.*, c.name, c.name_kr, c.image_url "
        "FROM character_relations cr "
        "JOIN characters c ON cr.char_from = c.id "
        "WHERE cr.char_to = ?",
        (character_id,),
    )

    # Quotes by this character
    quotes = db.fetchall(
        "SELECT q.*, e.title as episode_title, e.title_kr as episode_title_kr "
        "FROM quotes q "
        "LEFT JOIN episodes e ON q.episode_id = e.id "
        "WHERE q.character_id = ? ORDER BY q.id",
        (character_id,),
    )

    # Voice actors for this character
    voice_actors = db.fetchall(
        "SELECT * FROM voice_actors WHERE character_id = ? ORDER BY language",
        (character_id,),
    )

    # Abilities of this character
    abilities = db.fetchall(
        "SELECT * FROM abilities WHERE character_id = ? ORDER BY power_level DESC",
        (character_id,),
    )

    return {
        **dict(character),
        "relations": [dict(r) for r in relations_out] + [dict(r) for r in relations_in],
        "quotes": [dict(q) for q in quotes],
        "voice_actors": [dict(va) for va in voice_actors],
        "abilities": [dict(a) for a in abilities],
    }


# === Episodes ===

@app.get("/api/episodes")
def episodes_list(
    season: int = Query(None, description="Filter by season number"),
):
    """List all episodes with optional season filter."""
    db = get_db()
    if season is not None:
        rows = db.fetchall(
            "SELECT * FROM episodes WHERE season = ? ORDER BY episode_no",
            (season,),
        )
    else:
        rows = db.fetchall("SELECT * FROM episodes ORDER BY episode_no")
    return {"episodes": [dict(r) for r in rows], "total": len(rows)}


@app.get("/api/episodes/{episode_id}")
def episode_detail(episode_id: int):
    """Get a single episode by ID."""
    db = get_db()
    episode = db.fetchone("SELECT * FROM episodes WHERE id = ?", (episode_id,))
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return dict(episode)


# === Quotes ===

@app.get("/api/quotes")
def quotes_list(
    character_id: int = Query(None, description="Filter by character ID"),
):
    """List quotes with optional character filter."""
    db = get_db()
    if character_id is not None:
        rows = db.fetchall(
            "SELECT q.*, c.name as character_name, c.name_kr as character_name_kr "
            "FROM quotes q "
            "LEFT JOIN characters c ON q.character_id = c.id "
            "WHERE q.character_id = ? ORDER BY q.id",
            (character_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT q.*, c.name as character_name, c.name_kr as character_name_kr "
            "FROM quotes q "
            "LEFT JOIN characters c ON q.character_id = c.id "
            "ORDER BY q.id"
        )
    return {"quotes": [dict(r) for r in rows], "total": len(rows)}


# === Items ===

@app.get("/api/items")
def items_list(
    category: str = Query(None, description="Filter by category (weapon, gadget, vehicle, other)"),
):
    """List items with optional category filter."""
    db = get_db()
    if category:
        rows = db.fetchall(
            "SELECT * FROM items WHERE category = ? ORDER BY id",
            (category,),
        )
    else:
        rows = db.fetchall("SELECT * FROM items ORDER BY id")
    return {"items": [dict(r) for r in rows], "total": len(rows)}


# === Graph (D3.js Force Graph) ===

@app.get("/api/graph")
def graph():
    """D3.js force graph data: character nodes + relation links."""
    db = get_db()

    # Nodes: all characters
    characters = db.fetchall("SELECT id, name, name_kr, race, platoon, color, image_url FROM characters")
    nodes = []
    for c in characters:
        nodes.append({
            "id": c["id"],
            "name": c["name"],
            "name_kr": c["name_kr"],
            "race": c["race"],
            "platoon": c["platoon"] or "",
            "color": c["color"] or "",
            "image_url": c["image_url"] or "",
        })

    # Links: character relations
    relations = db.fetchall(
        "SELECT char_from as source, char_to as target, relation_type, description "
        "FROM character_relations"
    )
    links = [dict(r) for r in relations]

    # Platoon colors for grouping
    platoon_colors = {
        "Keroro Platoon": "#00aa00",
        "Garuru Platoon": "#0066cc",
        "Shurara Corps": "#cc0000",
    }

    return {"nodes": nodes, "links": links, "platoon_colors": platoon_colors}


# === World (Three.js 3D Data) ===

@app.get("/api/world")
def world():
    """Three.js 3D visualization data: characters grouped by platoon with positions."""
    db = get_db()

    # Get all characters grouped by platoon
    platoons = db.fetchall(
        "SELECT DISTINCT platoon FROM characters WHERE platoon IS NOT NULL AND platoon != '' ORDER BY platoon"
    )

    groups = []
    for i, p in enumerate(platoons):
        platoon_name = p["platoon"]
        members = db.fetchall(
            "SELECT id, name, name_kr, race, rank, color, image_url FROM characters WHERE platoon = ? ORDER BY id",
            (platoon_name,),
        )
        # Arrange members in a circle around the group center
        angle_step = (2 * math.pi) / max(len(members), 1)
        radius = 3.0
        group_x = (i % 3) * 15.0 - 15.0
        group_z = (i // 3) * 15.0 - 10.0

        member_list = []
        for j, m in enumerate(members):
            angle = j * angle_step
            member_list.append({
                **dict(m),
                "x": group_x + radius * math.cos(angle),
                "y": 0.0,
                "z": group_z + radius * math.sin(angle),
            })

        groups.append({
            "platoon": platoon_name,
            "center": {"x": group_x, "y": 0, "z": group_z},
            "members": member_list,
        })

    # Unaffiliated characters
    unaffiliated = db.fetchall(
        "SELECT id, name, name_kr, race, rank, color, image_url FROM characters "
        "WHERE platoon IS NULL OR platoon = '' ORDER BY id"
    )
    if unaffiliated:
        member_list = []
        angle_step = (2 * math.pi) / max(len(unaffiliated), 1)
        group_x = 0.0
        group_z = 20.0
        for j, m in enumerate(unaffiliated):
            angle = j * angle_step
            member_list.append({
                **dict(m),
                "x": group_x + 4.0 * math.cos(angle),
                "y": 0.0,
                "z": group_z + 4.0 * math.sin(angle),
            })
        groups.append({
            "platoon": "Unaffiliated",
            "center": {"x": group_x, "y": 0, "z": group_z},
            "members": member_list,
        })

    return {"groups": groups}


# === Stats ===

@app.get("/api/stats")
def stats():
    """Database statistics overview."""
    db = get_db()
    engine = SearchEngine(db)
    base_stats = engine.get_stats()

    # Add counts for new tables
    new_tables = ["invasion_plans", "abilities", "ost", "voice_actors", "military_ranks", "character_votes"]
    for table in new_tables:
        try:
            row = db.fetchone(f"SELECT COUNT(*) as cnt FROM {table}")
            base_stats[table] = row["cnt"] if row else 0
        except Exception:
            base_stats[table] = 0

    return base_stats


# === Visitor Count ===

@app.get("/api/visitor")
def get_visitor_count():
    """Get current visitor count."""
    db = get_db()
    row = db.fetchone("SELECT count FROM visitor_count WHERE id = 1")
    return {"count": row["count"] if row else 0}


@app.post("/api/visitor")
def increment_visitor_count(request: Request):
    """Increment visitor count."""
    client_ip = get_client_ip(request)
    if not visitor_limiter.is_allowed(f"visitor:{client_ip}"):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    db = get_db()
    db.execute("UPDATE visitor_count SET count = count + 1 WHERE id = 1")
    row = db.fetchone("SELECT count FROM visitor_count WHERE id = 1")
    return {"count": row["count"] if row else 0}


# === Guestbook ===

@app.get("/api/guestbook")
def list_guestbook(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List guestbook entries with pagination."""
    db = get_db()
    offset = (page - 1) * per_page
    rows = db.fetchall(
        "SELECT * FROM guestbook ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (per_page, offset),
    )
    total_row = db.fetchone("SELECT COUNT(*) as cnt FROM guestbook")
    total = total_row["cnt"] if total_row else 0
    return {
        "messages": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total / per_page) if per_page else 0,
    }


@app.post("/api/guestbook")
def create_guestbook(entry: GuestbookEntry, request: Request):
    """Create a new guestbook entry."""
    client_ip = get_client_ip(request)
    if not post_limiter.is_allowed(f"guestbook:{client_ip}"):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    db = get_db()
    cursor = db.execute(
        "INSERT INTO guestbook (nickname, message, keroro_pick) VALUES (?, ?, ?)",
        (entry.nickname.strip(), entry.message.strip(), entry.keroro_pick.strip()),
    )
    row = db.fetchone(
        "SELECT * FROM guestbook WHERE id = ?",
        (cursor.lastrowid,),
    )
    return dict(row)


@app.delete("/api/guestbook/{entry_id}")
def delete_guestbook(entry_id: int):
    """Delete a guestbook entry."""
    db = get_db()
    existing = db.fetchone("SELECT id FROM guestbook WHERE id = ?", (entry_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Guestbook entry not found")
    db.execute("DELETE FROM guestbook WHERE id = ?", (entry_id,))
    return {"deleted": True, "id": entry_id}


# === Board ===

@app.get("/api/board")
def list_board(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: str = Query(None, description="Filter by category"),
):
    """List board posts with pagination and optional category filter."""
    db = get_db()
    offset = (page - 1) * per_page

    if category:
        rows = db.fetchall(
            "SELECT * FROM board WHERE category = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (category, per_page, offset),
        )
        total_row = db.fetchone(
            "SELECT COUNT(*) as cnt FROM board WHERE category = ?",
            (category,),
        )
    else:
        rows = db.fetchall(
            "SELECT * FROM board ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (per_page, offset),
        )
        total_row = db.fetchone("SELECT COUNT(*) as cnt FROM board")

    total = total_row["cnt"] if total_row else 0
    return {
        "posts": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total / per_page) if per_page else 0,
    }


@app.post("/api/board")
def create_board_post(entry: BoardEntry, request: Request):
    """Create a new board post."""
    client_ip = get_client_ip(request)
    if not post_limiter.is_allowed(f"board:{client_ip}"):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    db = get_db()
    cursor = db.execute(
        "INSERT INTO board (author, title, content, category) VALUES (?, ?, ?, ?)",
        (entry.author.strip(), entry.title.strip(), entry.content.strip(), entry.category.strip()),
    )
    row = db.fetchone("SELECT * FROM board WHERE id = ?", (cursor.lastrowid,))
    return dict(row)


@app.delete("/api/board/{post_id}")
def delete_board_post(post_id: int):
    """Delete a board post."""
    db = get_db()
    existing = db.fetchone("SELECT id FROM board WHERE id = ?", (post_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Post not found")
    db.execute("DELETE FROM board WHERE id = ?", (post_id,))
    return {"deleted": True, "id": post_id}


# === Invasion Plans ===

@app.get("/api/invasion-plans")
def invasion_plans_list(
    result: str = Query(None, description="Filter by result (failure, partial, interrupted)"),
):
    """List all invasion plans with optional result filter."""
    db = get_db()
    if result:
        rows = db.fetchall(
            "SELECT ip.*, c.name as planner_name, c.name_kr as planner_name_kr "
            "FROM invasion_plans ip "
            "LEFT JOIN characters c ON ip.planner_id = c.id "
            "WHERE ip.result = ? ORDER BY ip.id",
            (result,),
        )
    else:
        rows = db.fetchall(
            "SELECT ip.*, c.name as planner_name, c.name_kr as planner_name_kr "
            "FROM invasion_plans ip "
            "LEFT JOIN characters c ON ip.planner_id = c.id "
            "ORDER BY ip.id"
        )
    return {"invasion_plans": [dict(r) for r in rows], "total": len(rows)}


@app.get("/api/invasion-plans/{plan_id}")
def invasion_plan_detail(plan_id: int):
    """Get a single invasion plan by ID."""
    db = get_db()
    plan = db.fetchone(
        "SELECT ip.*, c.name as planner_name, c.name_kr as planner_name_kr, "
        "e.title as episode_title, e.title_kr as episode_title_kr "
        "FROM invasion_plans ip "
        "LEFT JOIN characters c ON ip.planner_id = c.id "
        "LEFT JOIN episodes e ON ip.episode_id = e.id "
        "WHERE ip.id = ?",
        (plan_id,),
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Invasion plan not found")
    return dict(plan)


# === Abilities ===

@app.get("/api/abilities")
def abilities_list(
    character_id: int = Query(None, description="Filter by character ID"),
    type: str = Query(None, description="Filter by type (attack, defense, support, passive, special)"),
):
    """List all abilities with optional filters."""
    db = get_db()
    where_clauses = []
    params: list = []
    if character_id is not None:
        where_clauses.append("a.character_id = ?")
        params.append(character_id)
    if type:
        where_clauses.append("a.type = ?")
        params.append(type)

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    rows = db.fetchall(
        f"SELECT a.*, c.name as character_name, c.name_kr as character_name_kr "
        f"FROM abilities a "
        f"LEFT JOIN characters c ON a.character_id = c.id"
        f"{where_sql} ORDER BY a.power_level DESC",
        tuple(params),
    )
    return {"abilities": [dict(r) for r in rows], "total": len(rows)}


@app.get("/api/abilities/{ability_id}")
def ability_detail(ability_id: int):
    """Get a single ability by ID."""
    db = get_db()
    ability = db.fetchone(
        "SELECT a.*, c.name as character_name, c.name_kr as character_name_kr "
        "FROM abilities a "
        "LEFT JOIN characters c ON a.character_id = c.id "
        "WHERE a.id = ?",
        (ability_id,),
    )
    if not ability:
        raise HTTPException(status_code=404, detail="Ability not found")
    return dict(ability)


# === OST / Music ===

@app.get("/api/ost")
def ost_list(
    type: str = Query(None, description="Filter by type (opening, ending, insert, character)"),
    season: int = Query(None, description="Filter by season"),
):
    """List all OST entries with optional filters."""
    db = get_db()
    where_clauses = []
    params: list = []
    if type:
        where_clauses.append("type = ?")
        params.append(type)
    if season is not None:
        where_clauses.append("season = ?")
        params.append(season)

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    rows = db.fetchall(
        f"SELECT * FROM ost{where_sql} ORDER BY season, episode_start",
        tuple(params),
    )
    return {"ost": [dict(r) for r in rows], "total": len(rows)}


@app.get("/api/ost/{ost_id}")
def ost_detail(ost_id: int):
    """Get a single OST entry by ID."""
    db = get_db()
    entry = db.fetchone("SELECT * FROM ost WHERE id = ?", (ost_id,))
    if not entry:
        raise HTTPException(status_code=404, detail="OST entry not found")
    return dict(entry)


# === Voice Actors ===

@app.get("/api/voice-actors")
def voice_actors_list(
    character_id: int = Query(None, description="Filter by character ID"),
    language: str = Query(None, description="Filter by language (ja, ko)"),
):
    """List all voice actors with optional filters."""
    db = get_db()
    where_clauses = []
    params: list = []
    if character_id is not None:
        where_clauses.append("va.character_id = ?")
        params.append(character_id)
    if language:
        where_clauses.append("va.language = ?")
        params.append(language)

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    rows = db.fetchall(
        f"SELECT va.*, c.name as character_name, c.name_kr as character_name_kr "
        f"FROM voice_actors va "
        f"LEFT JOIN characters c ON va.character_id = c.id"
        f"{where_sql} ORDER BY va.character_id, va.language",
        tuple(params),
    )
    return {"voice_actors": [dict(r) for r in rows], "total": len(rows)}


@app.get("/api/voice-actors/{actor_id}")
def voice_actor_detail(actor_id: int):
    """Get a single voice actor entry by ID."""
    db = get_db()
    actor = db.fetchone(
        "SELECT va.*, c.name as character_name, c.name_kr as character_name_kr "
        "FROM voice_actors va "
        "LEFT JOIN characters c ON va.character_id = c.id "
        "WHERE va.id = ?",
        (actor_id,),
    )
    if not actor:
        raise HTTPException(status_code=404, detail="Voice actor not found")
    return dict(actor)


# === Military Ranks ===

@app.get("/api/ranks")
def ranks_list():
    """List all military ranks ordered by rank level descending."""
    db = get_db()
    rows = db.fetchall("SELECT * FROM military_ranks ORDER BY rank_level DESC")
    return {"ranks": [dict(r) for r in rows], "total": len(rows)}


# === Voting ===

vote_limiter = SimpleRateLimiter(max_requests=5, window_seconds=60)


@app.get("/api/votes")
def votes_list():
    """Get vote counts per character, grouped and ordered by count descending."""
    db = get_db()
    rows = db.fetchall(
        "SELECT cv.character_id, c.name, c.name_kr, c.image_url, COUNT(*) as vote_count "
        "FROM character_votes cv "
        "LEFT JOIN characters c ON cv.character_id = c.id "
        "GROUP BY cv.character_id "
        "ORDER BY vote_count DESC"
    )
    return {"votes": [dict(r) for r in rows], "total": len(rows)}


@app.post("/api/votes")
def cast_vote(entry: VoteEntry, request: Request):
    """Cast a vote for a character."""
    client_ip = get_client_ip(request)
    if not vote_limiter.is_allowed(f"vote:{client_ip}"):
        raise HTTPException(status_code=429, detail="Too many votes. Please try again later.")

    db = get_db()
    # Verify character exists
    character = db.fetchone("SELECT id, name, name_kr FROM characters WHERE id = ?", (entry.character_id,))
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    nickname = entry.voter_nickname.strip() or "anonymous"
    cursor = db.execute(
        "INSERT INTO character_votes (character_id, voter_nickname) VALUES (?, ?)",
        (entry.character_id, nickname),
    )
    return {
        "success": True,
        "vote_id": cursor.lastrowid,
        "character_name": character["name"],
        "character_name_kr": character["name_kr"],
    }


@app.get("/api/votes/ranking")
def votes_ranking():
    """Top 10 most voted characters."""
    db = get_db()
    rows = db.fetchall(
        "SELECT cv.character_id, c.name, c.name_kr, c.image_url, c.race, c.platoon, "
        "COUNT(*) as vote_count "
        "FROM character_votes cv "
        "LEFT JOIN characters c ON cv.character_id = c.id "
        "GROUP BY cv.character_id "
        "ORDER BY vote_count DESC LIMIT 10"
    )
    return {"ranking": [dict(r) for r in rows]}


# === Quiz ===

@app.get("/api/quiz/random")
def quiz_random():
    """Generate a random quiz question from DB or dynamic types."""
    db = get_db()

    # 60% chance: use pre-made quiz_questions table (89 questions)
    # 40% chance: use dynamic generation
    use_db = random.random() < 0.6
    if use_db:
        try:
            q = db.fetchone("SELECT * FROM quiz_questions ORDER BY RANDOM() LIMIT 1")
            if q:
                q = dict(q)
                options = [q["option_a"], q["option_b"], q["option_c"], q["option_d"]]
                correct_letter = q["correct_answer"]  # 'A','B','C','D'
                correct_idx = ord(correct_letter) - ord('A')
                return {
                    "type": "db_question",
                    "question": q["question"],
                    "options": options,
                    "correct_index": correct_idx,
                    "correct_answer": options[correct_idx],
                    "category": q.get("category", "general"),
                    "difficulty": q.get("difficulty", "normal"),
                }
        except Exception:
            pass  # fall through to dynamic

    quiz_types = [
        "character_by_description",
        "character_by_ability",
        "quote_author",
        "episode_season",
        "invasion_result",
    ]
    quiz_type = random.choice(quiz_types)

    quiz_dispatch = {
        "character_by_description": _quiz_character_by_description,
        "character_by_ability": _quiz_character_by_ability,
        "quote_author": _quiz_quote_author,
        "episode_season": _quiz_episode_season,
        "invasion_result": _quiz_invasion_result,
    }

    handler = quiz_dispatch.get(quiz_type, _quiz_character_by_description)
    try:
        return handler(db)
    except (HTTPException, ValueError, KeyError, IndexError):
        logger.warning("Quiz type '%s' failed, falling back to character_by_description", quiz_type)
        return _quiz_character_by_description(db)


def _quiz_character_by_description(db: Database) -> dict:
    """Quiz: given a description, guess the character."""
    characters = db.fetchall(
        "SELECT id, name, name_kr, description FROM characters "
        "WHERE description IS NOT NULL AND description != '' "
        "ORDER BY RANDOM() LIMIT 4"
    )
    if len(characters) < 4:
        raise HTTPException(status_code=500, detail="Not enough data for quiz")

    correct = dict(characters[0])
    options = [dict(c)["name_kr"] for c in characters]
    random.shuffle(options)
    correct_idx = options.index(correct["name_kr"])

    return {
        "type": "character_by_description",
        "question": correct["description"],
        "options": options,
        "correct_index": correct_idx,
        "correct_answer": correct["name_kr"],
        "hint": correct["name"],
    }


def _quiz_character_by_ability(db: Database) -> dict:
    """Quiz: given an ability, guess the character."""
    ability = db.fetchone(
        "SELECT a.*, c.name as character_name, c.name_kr as character_name_kr "
        "FROM abilities a "
        "JOIN characters c ON a.character_id = c.id "
        "ORDER BY RANDOM() LIMIT 1"
    )
    if not ability:
        return _quiz_character_by_description(db)

    ability = dict(ability)
    # Get 3 wrong character options
    wrong = db.fetchall(
        "SELECT DISTINCT name_kr FROM characters "
        "WHERE name_kr != ? ORDER BY RANDOM() LIMIT 3",
        (ability["character_name_kr"],),
    )
    options = [ability["character_name_kr"]] + [dict(w)["name_kr"] for w in wrong]
    random.shuffle(options)
    correct_idx = options.index(ability["character_name_kr"])

    return {
        "type": "character_by_ability",
        "question": f"'{ability['name_kr']}' - {ability['description']}",
        "options": options,
        "correct_index": correct_idx,
        "correct_answer": ability["character_name_kr"],
        "hint": ability["name"],
    }


def _quiz_quote_author(db: Database) -> dict:
    """Quiz: given a quote, guess who said it."""
    quote = db.fetchone(
        "SELECT q.*, c.name, c.name_kr "
        "FROM quotes q "
        "JOIN characters c ON q.character_id = c.id "
        "WHERE q.content_kr IS NOT NULL AND q.content_kr != '' "
        "ORDER BY RANDOM() LIMIT 1"
    )
    if not quote:
        return _quiz_character_by_description(db)

    quote = dict(quote)
    wrong = db.fetchall(
        "SELECT DISTINCT name_kr FROM characters "
        "WHERE name_kr != ? ORDER BY RANDOM() LIMIT 3",
        (quote["name_kr"],),
    )
    options = [quote["name_kr"]] + [dict(w)["name_kr"] for w in wrong]
    random.shuffle(options)
    correct_idx = options.index(quote["name_kr"])

    return {
        "type": "quote_author",
        "question": f'"{quote["content_kr"]}"',
        "options": options,
        "correct_index": correct_idx,
        "correct_answer": quote["name_kr"],
        "hint": quote.get("context", ""),
    }


def _quiz_episode_season(db: Database) -> dict:
    """Quiz: given an episode title, guess the season."""
    episode = db.fetchone(
        "SELECT * FROM episodes "
        "WHERE title_kr IS NOT NULL AND title_kr != '' "
        "ORDER BY RANDOM() LIMIT 1"
    )
    if not episode:
        return _quiz_character_by_description(db)

    episode = dict(episode)
    seasons = db.fetchall("SELECT DISTINCT season FROM episodes ORDER BY season")
    season_list = [str(dict(s)["season"]) for s in seasons]

    # Ensure we have 4 options
    correct = str(episode["season"])
    wrong_seasons = [s for s in season_list if s != correct]
    if len(wrong_seasons) < 3:
        # Pad with made-up season numbers
        all_possible = [str(i) for i in range(1, 8)]
        wrong_seasons = [s for s in all_possible if s != correct]
    wrong_seasons = wrong_seasons[:3]
    options = [correct] + wrong_seasons
    random.shuffle(options)

    options_labeled = [f"Season {s}" for s in options]
    correct_label = f"Season {correct}"
    correct_idx = options_labeled.index(correct_label)

    return {
        "type": "episode_season",
        "question": f"'{episode['title_kr']}' (EP {episode['episode_no']})",
        "options": options_labeled,
        "correct_index": correct_idx,
        "correct_answer": correct_label,
        "hint": episode.get("title", ""),
    }


def _quiz_invasion_result(db: Database) -> dict:
    """Quiz: given an invasion plan, guess the result."""
    plan = db.fetchone(
        "SELECT ip.*, c.name_kr as planner_name_kr "
        "FROM invasion_plans ip "
        "LEFT JOIN characters c ON ip.planner_id = c.id "
        "ORDER BY RANDOM() LIMIT 1"
    )
    if not plan:
        return _quiz_character_by_description(db)

    plan = dict(plan)
    result_options = ["failure", "partial", "interrupted"]
    correct = plan["result"]
    if correct not in result_options:
        result_options.append(correct)

    result_labels = {
        "failure": "Failure (complete failure)",
        "partial": "Partial (partial success)",
        "interrupted": "Interrupted (interrupted)",
    }
    options = [result_labels.get(r, r) for r in result_options]
    random.shuffle(options)

    correct_label = result_labels.get(correct, correct)
    correct_idx = options.index(correct_label) if correct_label in options else 0

    return {
        "type": "invasion_result",
        "question": f"{plan['name_kr']} - {plan['method']}",
        "options": options,
        "correct_index": correct_idx,
        "correct_answer": correct_label,
        "hint": plan.get("planner_name_kr", ""),
    }


# === Trivia ===


@app.get("/api/trivia")
def list_trivia(category: str = Query("", description="Filter by category")):
    """List all trivia facts, optionally filtered by category."""
    db = get_db()
    try:
        if category:
            rows = db.fetchall(
                "SELECT * FROM trivia WHERE category = ? ORDER BY id", (category,)
            )
        else:
            rows = db.fetchall("SELECT * FROM trivia ORDER BY id")
        return {"trivia": [dict(r) for r in rows], "total": len(rows)}
    except Exception:
        return {"trivia": [], "total": 0}


@app.get("/api/trivia/random")
def trivia_random(count: int = Query(5, ge=1, le=20)):
    """Get random trivia facts."""
    db = get_db()
    try:
        rows = db.fetchall(
            "SELECT * FROM trivia ORDER BY RANDOM() LIMIT ?", (count,)
        )
        return {"trivia": [dict(r) for r in rows]}
    except Exception:
        return {"trivia": []}


# === Analytics (MAL Crawled Data) ===

@app.get("/api/analytics/overview")
def analytics_overview():
    """Get MAL analytics overview: anime details, stats summary."""
    db = get_db()
    # Main TV series
    anime = db.fetchone("SELECT * FROM mal_anime WHERE key = 'tv'")
    if not anime:
        return {"available": False, "message": "MAL data not yet crawled. Run the crawler first."}

    # All anime entries (TV + movies)
    all_anime = db.fetchall("SELECT mal_id, title, type, score, scored_by, rank, popularity, members, favorites, key FROM mal_anime ORDER BY key")

    # Statistics
    stats = db.fetchone("SELECT * FROM mal_statistics WHERE id = 1")

    # Counts
    char_count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_characters")
    ep_count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_episodes")
    review_count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_reviews")
    rec_count = db.fetchone("SELECT COUNT(*) as cnt FROM mal_recommendations")

    return {
        "available": True,
        "main_anime": dict(anime),
        "all_anime": [dict(a) for a in all_anime],
        "statistics": dict(stats) if stats else None,
        "counts": {
            "characters": char_count["cnt"] if char_count else 0,
            "episodes": ep_count["cnt"] if ep_count else 0,
            "reviews": review_count["cnt"] if review_count else 0,
            "recommendations": rec_count["cnt"] if rec_count else 0,
        },
    }


@app.get("/api/analytics/score-distribution")
def analytics_score_distribution():
    """Get MAL score distribution data for charts."""
    db = get_db()
    stats = db.fetchone("SELECT scores_json FROM mal_statistics WHERE id = 1")
    if not stats or not stats["scores_json"]:
        return {"scores": []}
    return {"scores": json.loads(stats["scores_json"])}


@app.get("/api/analytics/viewing-status")
def analytics_viewing_status():
    """Get MAL viewing status distribution."""
    db = get_db()
    stats = db.fetchone(
        "SELECT watching, completed, on_hold, dropped, plan_to_watch, total "
        "FROM mal_statistics WHERE id = 1"
    )
    if not stats:
        return {"statuses": []}
    return {
        "statuses": [
            {"label": "Watching", "label_kr": "시청 중", "value": stats["watching"]},
            {"label": "Completed", "label_kr": "완료", "value": stats["completed"]},
            {"label": "On Hold", "label_kr": "보류", "value": stats["on_hold"]},
            {"label": "Dropped", "label_kr": "중단", "value": stats["dropped"]},
            {"label": "Plan to Watch", "label_kr": "볼 예정", "value": stats["plan_to_watch"]},
        ],
        "total": stats["total"],
    }


@app.get("/api/analytics/characters")
def analytics_characters(limit: int = Query(30, ge=1, le=100)):
    """Get MAL character popularity ranking."""
    db = get_db()
    rows = db.fetchall(
        "SELECT mal_id, name, image_url, favorites, role "
        "FROM mal_characters ORDER BY favorites DESC LIMIT ?",
        (limit,),
    )
    return {"characters": [dict(r) for r in rows], "total": len(rows)}


@app.get("/api/analytics/episodes")
def analytics_episodes():
    """Get MAL episode data with scores for trend analysis."""
    db = get_db()
    rows = db.fetchall(
        "SELECT mal_id, title, title_japanese, aired, score, filler, recap "
        "FROM mal_episodes ORDER BY mal_id"
    )
    return {"episodes": [dict(r) for r in rows], "total": len(rows)}


@app.get("/api/analytics/reviews")
def analytics_reviews(limit: int = Query(20, ge=1, le=100)):
    """Get MAL user reviews."""
    db = get_db()
    rows = db.fetchall(
        "SELECT mal_id, username, score, date, review, tags, episodes_watched, "
        "is_spoiler, is_preliminary, reactions_json "
        "FROM mal_reviews ORDER BY date DESC LIMIT ?",
        (limit,),
    )
    results = []
    for r in rows:
        entry = dict(r)
        if entry.get("tags"):
            try:
                entry["tags"] = json.loads(entry["tags"])
            except (json.JSONDecodeError, TypeError):
                entry["tags"] = []
        if entry.get("reactions_json"):
            try:
                entry["reactions"] = json.loads(entry["reactions_json"])
            except (json.JSONDecodeError, TypeError):
                entry["reactions"] = {}
            del entry["reactions_json"]
        results.append(entry)
    return {"reviews": results, "total": len(results)}


@app.get("/api/analytics/review-scores")
def analytics_review_scores():
    """Get review score distribution for charts."""
    db = get_db()
    rows = db.fetchall(
        "SELECT score, COUNT(*) as count FROM mal_reviews GROUP BY score ORDER BY score"
    )
    return {"scores": [dict(r) for r in rows]}


@app.get("/api/analytics/recommendations")
def analytics_recommendations(limit: int = Query(15, ge=1, le=50)):
    """Get MAL anime recommendations."""
    db = get_db()
    rows = db.fetchall(
        "SELECT mal_id, title, image_url, votes "
        "FROM mal_recommendations ORDER BY votes DESC LIMIT ?",
        (limit,),
    )
    return {"recommendations": [dict(r) for r in rows], "total": len(rows)}


@app.get("/api/analytics/movies")
def analytics_movies():
    """Get movie comparison data."""
    db = get_db()
    rows = db.fetchall(
        "SELECT mal_id, title, title_english, type, score, scored_by, rank, "
        "popularity, members, favorites, year, image_url, key "
        "FROM mal_anime WHERE type = 'Movie' ORDER BY year"
    )
    return {"movies": [dict(r) for r in rows], "total": len(rows)}


# === Extended Analytics (Staff, Manga, Relations, AniList) ===


@app.get("/api/analytics/staff")
def analytics_staff(limit: int = Query(217, ge=1, le=300)):
    """Get MAL staff/creators data with images."""
    db = get_db()
    rows = db.fetchall(
        "SELECT mal_id, name, image_url, positions_json FROM mal_staff LIMIT ?",
        (limit,),
    )
    results = []
    for r in rows:
        entry = dict(r)
        if entry.get("positions_json"):
            try:
                entry["positions"] = json.loads(entry["positions_json"])
            except (json.JSONDecodeError, TypeError):
                entry["positions"] = []
            del entry["positions_json"]
        else:
            entry["positions"] = []
        results.append(entry)

    # Aggregate position counts
    position_counts = defaultdict(int)
    for s in results:
        for pos in s["positions"]:
            position_counts[pos] += 1
    top_positions = sorted(position_counts.items(), key=lambda x: x[1], reverse=True)[:20]

    # Staff with images for gallery (filter out placeholder images)
    staff_with_images = [s for s in results if s.get("image_url") and "questionmark" not in s["image_url"]]

    return {
        "staff": results,
        "staff_with_images": staff_with_images[:60],
        "total": len(results),
        "position_counts": top_positions,
    }


@app.get("/api/analytics/relations")
def analytics_relations():
    """Get MAL franchise/related works map."""
    db = get_db()
    rows = db.fetchall(
        "SELECT mal_id, type, name, url, relation FROM mal_relations ORDER BY relation"
    )
    results = [dict(r) for r in rows]

    # Group by relation type
    grouped = defaultdict(list)
    for r in results:
        grouped[r["relation"]].append(r)

    return {"relations": results, "grouped": dict(grouped), "total": len(results)}


@app.get("/api/analytics/manga")
def analytics_manga():
    """Get MAL manga data for comparison with anime."""
    db = get_db()
    manga = db.fetchone("SELECT * FROM mal_manga LIMIT 1")
    if not manga:
        return {"available": False}

    manga_chars = db.fetchall(
        "SELECT mal_id, name, image_url, role FROM mal_manga_characters ORDER BY "
        "CASE WHEN role='Main' THEN 0 ELSE 1 END, name LIMIT 50"
    )

    return {
        "available": True,
        "manga": dict(manga),
        "characters": [dict(c) for c in manga_chars],
        "character_count": len(manga_chars),
    }


@app.get("/api/analytics/anilist")
def analytics_anilist():
    """Get AniList data for cross-platform comparison."""
    db = get_db()
    anilist = db.fetchone("SELECT * FROM anilist_anime LIMIT 1")
    if not anilist:
        return {"available": False}

    entry = dict(anilist)
    # Parse JSON fields
    for field in ["genres_json", "tags_json", "studios_json", "stats_json",
                  "rankings_json", "relations_json", "recommendations_json"]:
        key = field.replace("_json", "")
        if entry.get(field):
            try:
                entry[key] = json.loads(entry[field])
            except (json.JSONDecodeError, TypeError):
                entry[key] = []
            del entry[field]
        else:
            entry[key] = []
            if field in entry:
                del entry[field]

    return {"available": True, "anilist": entry}


@app.get("/api/analytics/anilist-characters")
def analytics_anilist_characters(limit: int = Query(30, ge=1, le=100)):
    """Get AniList character popularity data."""
    db = get_db()
    rows = db.fetchall(
        "SELECT anilist_id, name, name_native, image_url, favourites, role "
        "FROM anilist_characters ORDER BY favourites DESC LIMIT ?",
        (limit,),
    )
    return {"characters": [dict(r) for r in rows], "total": len(rows)}


@app.get("/api/analytics/comparison")
def analytics_comparison():
    """Cross-platform comparison: MAL vs AniList."""
    db = get_db()

    mal = db.fetchone("SELECT score, scored_by, rank, popularity, members, favorites FROM mal_anime WHERE key = 'tv'")
    anilist = db.fetchone("SELECT average_score, mean_score, popularity, favourites FROM anilist_anime LIMIT 1")
    manga = db.fetchone("SELECT score, scored_by, rank, popularity, members, chapters, volumes FROM mal_manga LIMIT 1")

    comparison = {
        "mal": dict(mal) if mal else None,
        "anilist": dict(anilist) if anilist else None,
        "manga": dict(manga) if manga else None,
    }

    # Score comparison
    if mal and anilist:
        comparison["score_comparison"] = {
            "mal_score": mal["score"],
            "mal_scored_by": mal["scored_by"],
            "anilist_score": anilist["average_score"],
            "anilist_mean": anilist["mean_score"],
            "difference": round(abs((mal["score"] or 0) - (anilist["average_score"] or 0) / 10), 2),
        }

    # Character popularity comparison with images (MAL vs AniList)
    mal_chars = db.fetchall(
        "SELECT name, image_url, favorites FROM mal_characters WHERE favorites > 0 ORDER BY favorites DESC LIMIT 10"
    )
    anilist_chars = db.fetchall(
        "SELECT name, image_url, favourites FROM anilist_characters WHERE favourites > 0 ORDER BY favourites DESC LIMIT 10"
    )
    comparison["character_comparison"] = {
        "mal": [dict(c) for c in mal_chars],
        "anilist": [dict(c) for c in anilist_chars],
    }

    return comparison


@app.get("/api/analytics/gallery")
def analytics_gallery():
    """Get all available images for gallery display."""
    db = get_db()

    # Anime posters (all 8 entries)
    anime_posters = db.fetchall(
        "SELECT mal_id, title, title_english, type, score, year, image_url, key "
        "FROM mal_anime WHERE image_url IS NOT NULL AND image_url != '' ORDER BY key"
    )

    # Recommendations with images
    rec_images = db.fetchall(
        "SELECT mal_id, title, image_url, votes FROM mal_recommendations "
        "WHERE image_url IS NOT NULL AND image_url != '' ORDER BY votes DESC LIMIT 20"
    )

    # Top characters with images (MAL)
    char_images = db.fetchall(
        "SELECT mal_id, name, image_url, favorites, role FROM mal_characters "
        "WHERE image_url IS NOT NULL AND image_url != '' AND favorites > 0 "
        "ORDER BY favorites DESC LIMIT 30"
    )

    # AniList characters with images
    anilist_char_images = db.fetchall(
        "SELECT anilist_id, name, name_native, image_url, favourites, role FROM anilist_characters "
        "WHERE image_url IS NOT NULL AND image_url != '' "
        "ORDER BY favourites DESC LIMIT 30"
    )

    # AniList anime banner/cover
    anilist_anime = db.fetchone(
        "SELECT cover_image, banner_image, title_romaji FROM anilist_anime LIMIT 1"
    )

    # Manga characters with images
    manga_char_images = db.fetchall(
        "SELECT mal_id, name, image_url, role FROM mal_manga_characters "
        "WHERE image_url IS NOT NULL AND image_url != '' "
        "ORDER BY CASE WHEN role='Main' THEN 0 ELSE 1 END, name LIMIT 30"
    )

    return {
        "anime_posters": [dict(a) for a in anime_posters],
        "recommendations": [dict(r) for r in rec_images],
        "mal_characters": [dict(c) for c in char_images],
        "anilist_characters": [dict(c) for c in anilist_char_images],
        "anilist_banner": dict(anilist_anime) if anilist_anime else None,
        "manga_characters": [dict(m) for m in manga_char_images],
        "total_images": (
            len(anime_posters) + len(rec_images) + len(char_images)
            + len(anilist_char_images) + len(manga_char_images)
            + (2 if anilist_anime else 0)
        ),
    }


# === Main ===

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
