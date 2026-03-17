"""SQLite database connection and initialization for Keroro Archive"""

import os
import sqlite3

from config import DB_PATH


class Database:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self):
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, encoding="utf-8") as f:
                self.conn.executescript(f.read())

    def init_schema(self):
        """Public method for test fixtures."""
        self._init_schema()

    def execute(self, sql: str, params: tuple = ()):
        cursor = self.conn.execute(sql, params)
        self.conn.commit()
        return cursor

    def executemany(self, sql: str, params_list):
        cursor = self.conn.executemany(sql, params_list)
        self.conn.commit()
        return cursor

    def fetchone(self, sql: str, params: tuple = ()):
        return self.conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: tuple = ()):
        return self.conn.execute(sql, params).fetchall()

    def close(self):
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
