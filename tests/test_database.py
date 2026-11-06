"""
Unit tests for SQLite WAL persistence and save/load workflows.
"""

import pytest
import os
from server.database.connection import init_db, get_db
from server.simulation.engine import SimulationEngine

@pytest.mark.asyncio
async def test_database_initialization_and_save_load(tmp_path):
    test_db = str(tmp_path / "test_pax.sqlite3")
    os.environ["PAX_DB_PATH"] = test_db

    await init_db()

    # Check WAL mode
    async with get_db() as db:
        async with db.execute("PRAGMA journal_mode;") as cur:
            row = await cur.fetchone()
            assert row[0].lower() == "wal"

    # Test engine save and load
    test_engine = SimulationEngine()
    test_engine.clock.year = 5
    test_engine.clock.month = 4
    test_engine.world.nations["nation_prussia"]["gold"] = 9999

    save_id = await test_engine.save_state("Test Save")
    assert save_id is not None

    # Create fresh engine and load
    new_engine = SimulationEngine()
    loaded = await new_engine.load_state(save_id)
    assert loaded is True
    assert new_engine.clock.year == 5
    assert new_engine.clock.month == 4
    assert new_engine.world.nations["nation_prussia"]["gold"] == 9999
