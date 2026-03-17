"""FTS5-based search engine for Keroro Archive"""

import logging

from db.database import Database

logger = logging.getLogger(__name__)


class SearchEngine:
    def __init__(self, db: Database):
        self.db = db

    def search_all(self, query: str, limit: int = 20, offset: int = 0) -> dict:
        """Search characters, episodes, quotes, and items."""
        characters = self.search_characters(query, limit=limit, offset=offset)
        episodes = self.search_episodes(query, limit=limit, offset=offset)
        quotes = self.search_quotes(query, limit=limit, offset=offset)
        items = self.search_items(query, limit=limit, offset=offset)
        return {
            "characters": characters["items"],
            "characters_total": characters["total"],
            "episodes": episodes["items"],
            "episodes_total": episodes["total"],
            "quotes": quotes["items"],
            "quotes_total": quotes["total"],
            "items": items["items"],
            "items_total": items["total"],
        }

    def search_characters(self, query: str, limit: int = 20, offset: int = 0) -> dict:
        """Search characters using FTS5."""
        try:
            fts_query = self._build_fts_query(query)
            rows = self.db.fetchall(
                "SELECT c.* FROM characters c "
                "JOIN characters_fts fts ON c.id = fts.rowid "
                "WHERE characters_fts MATCH ? "
                "ORDER BY rank LIMIT ? OFFSET ?",
                (fts_query, limit, offset),
            )
            total_row = self.db.fetchone(
                "SELECT COUNT(*) as cnt FROM characters c "
                "JOIN characters_fts fts ON c.id = fts.rowid "
                "WHERE characters_fts MATCH ?",
                (fts_query,),
            )
            return {
                "items": [dict(r) for r in rows],
                "total": total_row["cnt"] if total_row else 0,
            }
        except Exception:
            return self._fallback_search(
                "characters",
                ["name", "name_kr", "race", "platoon", "description"],
                query, limit, offset,
            )

    def search_episodes(self, query: str, limit: int = 20, offset: int = 0) -> dict:
        """Search episodes using FTS5."""
        try:
            fts_query = self._build_fts_query(query)
            rows = self.db.fetchall(
                "SELECT e.* FROM episodes e "
                "JOIN episodes_fts fts ON e.id = fts.rowid "
                "WHERE episodes_fts MATCH ? "
                "ORDER BY rank LIMIT ? OFFSET ?",
                (fts_query, limit, offset),
            )
            total_row = self.db.fetchone(
                "SELECT COUNT(*) as cnt FROM episodes e "
                "JOIN episodes_fts fts ON e.id = fts.rowid "
                "WHERE episodes_fts MATCH ?",
                (fts_query,),
            )
            return {
                "items": [dict(r) for r in rows],
                "total": total_row["cnt"] if total_row else 0,
            }
        except Exception:
            return self._fallback_search(
                "episodes",
                ["title", "title_kr", "summary"],
                query, limit, offset,
            )

    def search_quotes(self, query: str, limit: int = 20, offset: int = 0) -> dict:
        """Search quotes using FTS5."""
        try:
            fts_query = self._build_fts_query(query)
            rows = self.db.fetchall(
                "SELECT q.*, c.name as character_name, c.name_kr as character_name_kr "
                "FROM quotes q "
                "JOIN quotes_fts fts ON q.id = fts.rowid "
                "LEFT JOIN characters c ON q.character_id = c.id "
                "WHERE quotes_fts MATCH ? "
                "ORDER BY rank LIMIT ? OFFSET ?",
                (fts_query, limit, offset),
            )
            total_row = self.db.fetchone(
                "SELECT COUNT(*) as cnt FROM quotes q "
                "JOIN quotes_fts fts ON q.id = fts.rowid "
                "WHERE quotes_fts MATCH ?",
                (fts_query,),
            )
            return {
                "items": [dict(r) for r in rows],
                "total": total_row["cnt"] if total_row else 0,
            }
        except Exception:
            return self._fallback_search(
                "quotes",
                ["content", "content_kr", "context"],
                query, limit, offset,
            )

    def search_items(self, query: str, limit: int = 20, offset: int = 0) -> dict:
        """Search items using FTS5."""
        try:
            fts_query = self._build_fts_query(query)
            rows = self.db.fetchall(
                "SELECT i.* FROM items i "
                "JOIN items_fts fts ON i.id = fts.rowid "
                "WHERE items_fts MATCH ? "
                "ORDER BY rank LIMIT ? OFFSET ?",
                (fts_query, limit, offset),
            )
            total_row = self.db.fetchone(
                "SELECT COUNT(*) as cnt FROM items i "
                "JOIN items_fts fts ON i.id = fts.rowid "
                "WHERE items_fts MATCH ?",
                (fts_query,),
            )
            return {
                "items": [dict(r) for r in rows],
                "total": total_row["cnt"] if total_row else 0,
            }
        except Exception:
            return self._fallback_search(
                "items",
                ["name", "name_kr", "description"],
                query, limit, offset,
            )

    def suggest(self, query: str, limit: int = 10) -> list:
        """Auto-suggest character names."""
        like = f"{query}%"
        rows = self.db.fetchall(
            "SELECT id, name, name_kr, race, platoon, image_url FROM characters "
            "WHERE name LIKE ? OR name_kr LIKE ? "
            "ORDER BY id LIMIT ?",
            (like, like, limit),
        )
        return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        """Get overall database statistics."""
        tables = ["characters", "episodes", "quotes", "items", "guestbook", "board"]
        stats = {}
        for table in tables:
            row = self.db.fetchone(f"SELECT COUNT(*) as cnt FROM {table}")
            stats[table] = row["cnt"] if row else 0

        # Additional breakdowns
        race_stats = self.db.fetchall(
            "SELECT race, COUNT(*) as cnt FROM characters "
            "GROUP BY race ORDER BY cnt DESC"
        )
        platoon_stats = self.db.fetchall(
            "SELECT platoon, COUNT(*) as cnt FROM characters "
            "WHERE platoon IS NOT NULL "
            "GROUP BY platoon ORDER BY cnt DESC"
        )
        season_stats = self.db.fetchall(
            "SELECT season, COUNT(*) as cnt FROM episodes "
            "GROUP BY season ORDER BY season"
        )

        stats["by_race"] = [dict(r) for r in race_stats]
        stats["by_platoon"] = [dict(r) for r in platoon_stats]
        stats["by_season"] = [dict(r) for r in season_stats]
        return stats

    def _fallback_search(
        self, table: str, columns: list, query: str, limit: int, offset: int
    ) -> dict:
        """Fallback LIKE search when FTS fails."""
        like = f"%{query}%"
        where_clauses = " OR ".join(f"{col} LIKE ?" for col in columns)
        params = tuple([like] * len(columns)) + (limit, offset)

        rows = self.db.fetchall(
            f"SELECT * FROM {table} WHERE {where_clauses} "
            f"ORDER BY id LIMIT ? OFFSET ?",
            params,
        )
        total_row = self.db.fetchone(
            f"SELECT COUNT(*) as cnt FROM {table} WHERE {where_clauses}",
            tuple([like] * len(columns)),
        )
        return {
            "items": [dict(r) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
        }

    def _build_fts_query(self, query: str) -> str:
        """Build FTS5 query from user input."""
        terms = query.strip().split()
        if len(terms) == 1:
            term = terms[0].replace('"', '')
            return f'"{term}" OR {term}*'
        escaped = [t.replace('"', '') for t in terms]
        return " OR ".join(f'"{t}"' for t in escaped)
