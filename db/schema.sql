-- Keroro Gunso Archive Database Schema
-- SQLite with FTS5 full-text search

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- Characters
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_kr TEXT,
    race TEXT DEFAULT 'Keronian',
    platoon TEXT,
    rank TEXT,
    color TEXT,
    ability TEXT,
    personality TEXT,
    description TEXT,
    image_url TEXT,
    first_appearance INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Character relations
CREATE TABLE IF NOT EXISTS character_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    char_from INTEGER NOT NULL,
    char_to INTEGER NOT NULL,
    relation_type TEXT NOT NULL DEFAULT 'friend',
    description TEXT,
    FOREIGN KEY (char_from) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (char_to) REFERENCES characters(id) ON DELETE CASCADE,
    UNIQUE(char_from, char_to, relation_type)
);

-- Episodes
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_no INTEGER UNIQUE NOT NULL,
    title TEXT NOT NULL,
    title_kr TEXT,
    air_date TEXT,
    season INTEGER DEFAULT 1,
    arc TEXT,
    summary TEXT
);

-- Quotes
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_kr TEXT,
    episode_id INTEGER,
    context TEXT,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (episode_id) REFERENCES episodes(id) ON DELETE SET NULL
);

-- Items (weapons, gadgets, vehicles)
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_kr TEXT,
    category TEXT DEFAULT 'other',
    owner TEXT,
    description TEXT,
    image_url TEXT
);

-- Community: Guestbook
CREATE TABLE IF NOT EXISTS guestbook (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nickname TEXT NOT NULL,
    message TEXT NOT NULL,
    keroro_pick TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);

-- Community: Board
CREATE TABLE IF NOT EXISTS board (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    created_at TEXT DEFAULT (datetime('now'))
);

-- Community: Visitor count
CREATE TABLE IF NOT EXISTS visitor_count (
    id INTEGER PRIMARY KEY,
    count INTEGER DEFAULT 0
);
INSERT OR IGNORE INTO visitor_count (id, count) VALUES (1, 0);

-- Indexes: Characters
CREATE INDEX IF NOT EXISTS idx_characters_race ON characters(race);
CREATE INDEX IF NOT EXISTS idx_characters_platoon ON characters(platoon);
CREATE INDEX IF NOT EXISTS idx_characters_color ON characters(color);
CREATE INDEX IF NOT EXISTS idx_characters_first_appearance ON characters(first_appearance);

-- Indexes: Character relations
CREATE INDEX IF NOT EXISTS idx_relations_from ON character_relations(char_from);
CREATE INDEX IF NOT EXISTS idx_relations_to ON character_relations(char_to);
CREATE INDEX IF NOT EXISTS idx_relations_type ON character_relations(relation_type);

-- Indexes: Episodes
CREATE INDEX IF NOT EXISTS idx_episodes_season ON episodes(season);
CREATE INDEX IF NOT EXISTS idx_episodes_air_date ON episodes(air_date);
CREATE INDEX IF NOT EXISTS idx_episodes_arc ON episodes(arc);

-- Indexes: Quotes
CREATE INDEX IF NOT EXISTS idx_quotes_character ON quotes(character_id);
CREATE INDEX IF NOT EXISTS idx_quotes_episode ON quotes(episode_id);

-- Indexes: Items
CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
CREATE INDEX IF NOT EXISTS idx_items_owner ON items(owner);

-- Indexes: Board
CREATE INDEX IF NOT EXISTS idx_board_category ON board(category);
CREATE INDEX IF NOT EXISTS idx_board_created ON board(created_at DESC);

-- Indexes: Guestbook
CREATE INDEX IF NOT EXISTS idx_guestbook_created ON guestbook(created_at DESC);

-- FTS5: Characters search
CREATE VIRTUAL TABLE IF NOT EXISTS characters_fts USING fts5(
    name, name_kr, race, platoon, description,
    content='characters', content_rowid='id',
    tokenize='unicode61'
);

-- FTS5: Episodes search
CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(
    title, title_kr, summary,
    content='episodes', content_rowid='id',
    tokenize='unicode61'
);

-- FTS5: Quotes search
CREATE VIRTUAL TABLE IF NOT EXISTS quotes_fts USING fts5(
    content, content_kr, context,
    content='quotes', content_rowid='id',
    tokenize='unicode61'
);

-- FTS5: Items search
CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
    name, name_kr, description,
    content='items', content_rowid='id',
    tokenize='unicode61'
);

-- FTS triggers: Characters INSERT
CREATE TRIGGER IF NOT EXISTS characters_ai AFTER INSERT ON characters BEGIN
    INSERT INTO characters_fts(rowid, name, name_kr, race, platoon, description)
    VALUES (new.id, new.name, new.name_kr, new.race, new.platoon, new.description);
END;

-- FTS triggers: Characters DELETE
CREATE TRIGGER IF NOT EXISTS characters_ad AFTER DELETE ON characters BEGIN
    INSERT INTO characters_fts(characters_fts, rowid, name, name_kr, race, platoon, description)
    VALUES ('delete', old.id, old.name, old.name_kr, old.race, old.platoon, old.description);
END;

-- FTS triggers: Characters UPDATE
CREATE TRIGGER IF NOT EXISTS characters_au AFTER UPDATE ON characters BEGIN
    INSERT INTO characters_fts(characters_fts, rowid, name, name_kr, race, platoon, description)
    VALUES ('delete', old.id, old.name, old.name_kr, old.race, old.platoon, old.description);
    INSERT INTO characters_fts(rowid, name, name_kr, race, platoon, description)
    VALUES (new.id, new.name, new.name_kr, new.race, new.platoon, new.description);
END;

-- FTS triggers: Episodes INSERT
CREATE TRIGGER IF NOT EXISTS episodes_ai AFTER INSERT ON episodes BEGIN
    INSERT INTO episodes_fts(rowid, title, title_kr, summary)
    VALUES (new.id, new.title, new.title_kr, new.summary);
END;

-- FTS triggers: Episodes DELETE
CREATE TRIGGER IF NOT EXISTS episodes_ad AFTER DELETE ON episodes BEGIN
    INSERT INTO episodes_fts(episodes_fts, rowid, title, title_kr, summary)
    VALUES ('delete', old.id, old.title, old.title_kr, old.summary);
END;

-- FTS triggers: Episodes UPDATE
CREATE TRIGGER IF NOT EXISTS episodes_au AFTER UPDATE ON episodes BEGIN
    INSERT INTO episodes_fts(episodes_fts, rowid, title, title_kr, summary)
    VALUES ('delete', old.id, old.title, old.title_kr, old.summary);
    INSERT INTO episodes_fts(rowid, title, title_kr, summary)
    VALUES (new.id, new.title, new.title_kr, new.summary);
END;

-- FTS triggers: Quotes INSERT
CREATE TRIGGER IF NOT EXISTS quotes_ai AFTER INSERT ON quotes BEGIN
    INSERT INTO quotes_fts(rowid, content, content_kr, context)
    VALUES (new.id, new.content, new.content_kr, new.context);
END;

-- FTS triggers: Quotes DELETE
CREATE TRIGGER IF NOT EXISTS quotes_ad AFTER DELETE ON quotes BEGIN
    INSERT INTO quotes_fts(quotes_fts, rowid, content, content_kr, context)
    VALUES ('delete', old.id, old.content, old.content_kr, old.context);
END;

-- FTS triggers: Quotes UPDATE
CREATE TRIGGER IF NOT EXISTS quotes_au AFTER UPDATE ON quotes BEGIN
    INSERT INTO quotes_fts(quotes_fts, rowid, content, content_kr, context)
    VALUES ('delete', old.id, old.content, old.content_kr, old.context);
    INSERT INTO quotes_fts(rowid, content, content_kr, context)
    VALUES (new.id, new.content, new.content_kr, new.context);
END;

-- FTS triggers: Items INSERT
CREATE TRIGGER IF NOT EXISTS items_ai AFTER INSERT ON items BEGIN
    INSERT INTO items_fts(rowid, name, name_kr, description)
    VALUES (new.id, new.name, new.name_kr, new.description);
END;

-- FTS triggers: Items DELETE
CREATE TRIGGER IF NOT EXISTS items_ad AFTER DELETE ON items BEGIN
    INSERT INTO items_fts(items_fts, rowid, name, name_kr, description)
    VALUES ('delete', old.id, old.name, old.name_kr, old.description);
END;

-- FTS triggers: Items UPDATE
CREATE TRIGGER IF NOT EXISTS items_au AFTER UPDATE ON items BEGIN
    INSERT INTO items_fts(items_fts, rowid, name, name_kr, description)
    VALUES ('delete', old.id, old.name, old.name_kr, old.description);
    INSERT INTO items_fts(rowid, name, name_kr, description)
    VALUES (new.id, new.name, new.name_kr, new.description);
END;

-- ============================================================
-- New Tables (Phase 2)
-- ============================================================

-- Invasion Plans (케로로의 지구 침략 작전)
CREATE TABLE IF NOT EXISTS invasion_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_kr TEXT NOT NULL,
    planner_id INTEGER,
    episode_id INTEGER,
    method TEXT NOT NULL,
    result TEXT NOT NULL DEFAULT 'failure',
    result_reason TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (planner_id) REFERENCES characters(id)
);

-- Abilities/Skills (필살기/특수능력)
CREATE TABLE IF NOT EXISTS abilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_kr TEXT NOT NULL,
    character_id INTEGER NOT NULL,
    type TEXT NOT NULL DEFAULT 'attack',
    power_level INTEGER DEFAULT 5,
    description TEXT,
    first_used_episode INTEGER,
    FOREIGN KEY (character_id) REFERENCES characters(id)
);

-- OST/Music (주제곡/삽입곡)
CREATE TABLE IF NOT EXISTS ost (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    title_kr TEXT,
    artist TEXT NOT NULL,
    type TEXT NOT NULL,
    season INTEGER,
    episode_start INTEGER,
    episode_end INTEGER,
    release_date TEXT,
    description TEXT
);

-- Voice Actors (성우)
CREATE TABLE IF NOT EXISTS voice_actors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    actor_name TEXT NOT NULL,
    actor_name_kr TEXT,
    language TEXT NOT NULL DEFAULT 'ja',
    other_roles TEXT,
    FOREIGN KEY (character_id) REFERENCES characters(id)
);

-- Military Ranks (케론군 계급체계)
CREATE TABLE IF NOT EXISTS military_ranks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rank_name TEXT NOT NULL,
    rank_name_kr TEXT NOT NULL,
    rank_level INTEGER NOT NULL,
    description TEXT,
    notable_holders TEXT
);

-- Character Votes (투표)
CREATE TABLE IF NOT EXISTS character_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    voter_nickname TEXT DEFAULT 'anonymous',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id)
);

-- FTS for new tables
CREATE VIRTUAL TABLE IF NOT EXISTS invasion_plans_fts USING fts5(
    name, name_kr, method, result_reason, description,
    content='invasion_plans', content_rowid='id'
);

CREATE VIRTUAL TABLE IF NOT EXISTS abilities_fts USING fts5(
    name, name_kr, type, description,
    content='abilities', content_rowid='id'
);

-- Triggers for invasion_plans FTS
CREATE TRIGGER IF NOT EXISTS invasion_plans_ai AFTER INSERT ON invasion_plans BEGIN
    INSERT INTO invasion_plans_fts(rowid, name, name_kr, method, result_reason, description)
    VALUES (new.id, new.name, new.name_kr, new.method, new.result_reason, new.description);
END;

CREATE TRIGGER IF NOT EXISTS invasion_plans_ad AFTER DELETE ON invasion_plans BEGIN
    INSERT INTO invasion_plans_fts(invasion_plans_fts, rowid, name, name_kr, method, result_reason, description)
    VALUES ('delete', old.id, old.name, old.name_kr, old.method, old.result_reason, old.description);
END;

-- Triggers for abilities FTS
CREATE TRIGGER IF NOT EXISTS abilities_ai AFTER INSERT ON abilities BEGIN
    INSERT INTO abilities_fts(rowid, name, name_kr, type, description)
    VALUES (new.id, new.name, new.name_kr, new.type, new.description);
END;

CREATE TRIGGER IF NOT EXISTS abilities_ad AFTER DELETE ON abilities BEGIN
    INSERT INTO abilities_fts(abilities_fts, rowid, name, name_kr, type, description)
    VALUES ('delete', old.id, old.name, old.name_kr, old.type, old.description);
END;

-- Indexes for new tables
CREATE INDEX IF NOT EXISTS idx_invasion_result ON invasion_plans(result);
CREATE INDEX IF NOT EXISTS idx_abilities_character ON abilities(character_id);
CREATE INDEX IF NOT EXISTS idx_abilities_type ON abilities(type);
CREATE INDEX IF NOT EXISTS idx_ost_type ON ost(type);
CREATE INDEX IF NOT EXISTS idx_ost_season ON ost(season);
CREATE INDEX IF NOT EXISTS idx_voice_actors_character ON voice_actors(character_id);
CREATE INDEX IF NOT EXISTS idx_voice_actors_language ON voice_actors(language);
CREATE INDEX IF NOT EXISTS idx_votes_character ON character_votes(character_id);
