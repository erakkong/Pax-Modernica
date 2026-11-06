-- Pax Modernica Database Schema (SQLite with WAL mode)

CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS game_saves (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    game_year INTEGER NOT NULL,
    game_month INTEGER NOT NULL,
    game_day INTEGER NOT NULL,
    tick_id INTEGER NOT NULL,
    world_state_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS world_chronicle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tick_id INTEGER NOT NULL,
    game_year INTEGER NOT NULL,
    game_month INTEGER NOT NULL,
    game_day INTEGER NOT NULL,
    category TEXT NOT NULL,
    headline TEXT NOT NULL,
    body TEXT NOT NULL,
    nation_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chronicle_tick ON world_chronicle(tick_id);
CREATE INDEX IF NOT EXISTS idx_sessions_account ON sessions(account_id);
