"""
Pax Modernica - Database Connection Manager
Provides async SQLite connection context manager with WAL mode and transaction support.
"""

import os
import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator

def get_db_path() -> str:
    return os.environ.get("PAX_DB_PATH", str(Path(__file__).resolve().parent.parent.parent / "pax_modernica.sqlite3"))

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Async context manager yielding a configured SQLite connection."""
    db_path = get_db_path()
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode = WAL;")
    await db.execute("PRAGMA synchronous = NORMAL;")
    await db.execute("PRAGMA foreign_keys = ON;")
    try:
        yield db
    finally:
        await db.close()

async def init_db() -> None:
    """Initializes the database schema if not already present."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    async with get_db() as db:
        await db.executescript(schema_sql)
        await db.commit()
