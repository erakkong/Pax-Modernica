"""
Pax Modernica - Authoritative Simulation Engine
Executes deterministic game ticks, budget cycles, events, and persistence.
"""

import asyncio
import json
import uuid
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from server.simulation.clock import GameClock
from server.simulation.world_state import WorldState
from server.database.connection import get_db

logger = logging.getLogger("pax_simulation")

class SimulationEngine:
    """Core game loop orchestrator and authoritative rule referee."""

    def __init__(self):
        self.clock = GameClock(is_paused=False)
        self.world = WorldState()
        self.is_running = False
        self._loop_task: Optional[asyncio.Task] = None
        self.broadcast_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None

    def start(self) -> None:
        """Starts the background asyncio simulation loop."""
        if not self.is_running:
            self.is_running = True
            self._loop_task = asyncio.create_task(self._simulation_loop())
            logger.info("Pax Modernica Simulation Engine gestartet.")

    def stop(self) -> None:
        """Stops the simulation loop gracefully."""
        self.is_running = False
        if self._loop_task:
            self._loop_task.cancel()
            self._loop_task = None
            logger.info("Pax Modernica Simulation Engine gestoppt.")

    async def _simulation_loop(self) -> None:
        """Fixed 1Hz tick loop (1 real second = 2 game minutes by default)."""
        while self.is_running:
            try:
                await asyncio.sleep(1.0)
                tick_result = self.clock.tick(1.0)

                if tick_result["advanced"]:
                    await self._process_tick(tick_result)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Fehler im Simulations-Tick: {e}", exc_info=True)

    async def _process_tick(self, tick_result: Dict[str, Any]) -> None:
        """Processes monthly economic payouts and world changes."""
        clock_data = tick_result["clock"]
        new_month = tick_result["new_month"]
        new_year = tick_result["new_year"]

        deltas: Dict[str, Any] = {
            "clock": clock_data,
            "nations": {},
            "events": []
        }

        if new_month:
            # Process national budgets: income from taxes - expenses
            for nid, nat in self.world.nations.items():
                net_change = nat["monthly_income"] - nat["monthly_expense"]
                nat["gold"] = round(nat["gold"] + net_change, 1)

                # Slow population growth (approx 0.1% monthly)
                for pid in nat["provinces"]:
                    prov = self.world.provinces[pid]
                    prov["population"] = int(prov["population"] * 1.001)

                deltas["nations"][nid] = {
                    "gold": nat["gold"],
                    "total_population": nat["total_population"],
                    "stability": nat["stability"]
                }

            # Periodic Auto-Save every 3 months
            if clock_data["month"] % 3 == 0:
                await self.save_state("auto_save")

        if new_year:
            # Generate annual milestone chronicle
            evt = self.world.add_chronicle_event(
                tick_id=clock_data["tick_id"],
                year=clock_data["year"],
                month=clock_data["month"],
                day=clock_data["day"],
                category="JAHRESWECHSEL",
                headline=f"Neues Spieljahr {clock_data['year']} angebrochen",
                body=f"Europa schreibt nun das Jahr {clock_data['year']} ({clock_data['historical_year']} n. Chr.). Die Märkte florieren und die Fürstenhäuser wachen über ihre Reiche."
            )
            deltas["events"].append(evt)

        # Broadcast tick updates to all active players
        if self.broadcast_callback:
            await self.broadcast_callback({
                "type": "TICK",
                "tick_id": clock_data["tick_id"],
                "clock": clock_data,
                "deltas": deltas if new_month or new_year else None
            })

    async def save_state(self, name: str = "manual_save") -> str:
        """Persists complete world state snapshot to SQLite database."""
        save_id = str(uuid.uuid4())
        state_json = json.dumps(self.world.to_dict())

        async with get_db() as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO game_saves (id, name, game_year, game_month, game_day, tick_id, world_state_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    save_id,
                    name,
                    self.clock.year,
                    self.clock.month,
                    self.clock.day,
                    self.clock.tick_id,
                    state_json
                )
            )
            await db.commit()
            logger.info(f"Spielstand '{name}' ({save_id}) erfolgreich in SQLite gesichert.")
            return save_id

    async def load_state(self, save_id: Optional[str] = None) -> bool:
        """Loads latest or specified game snapshot from SQLite database."""
        async with get_db() as db:
            query = "SELECT * FROM game_saves WHERE id = ?" if save_id else "SELECT * FROM game_saves ORDER BY updated_at DESC LIMIT 1"
            params = (save_id,) if save_id else ()
            async with db.execute(query, params) as cur:
                row = await cur.fetchone()
                if not row:
                    return False

                data = json.loads(row["world_state_json"])
                self.world.from_dict(data)
                self.clock.year = row["game_year"]
                self.clock.month = row["game_month"]
                self.clock.day = row["game_day"]
                self.clock.tick_id = row["tick_id"]
                logger.info(f"Spielstand geladen: Jahr {self.clock.year}, Monat {self.clock.month}")
                return True

    def process_action(self, action: Dict[str, Any], account_id: Optional[str] = None) -> Dict[str, Any]:
        """Validates and applies client gameplay commands."""
        action_type = action.get("type")

        if action_type == "PAUSE":
            paused = bool(action.get("paused", True))
            self.clock.set_paused(paused)
            return {"success": True, "action": "PAUSE", "paused": self.clock.is_paused}

        elif action_type == "SET_SPEED":
            speed = float(action.get("speed", 1.0))
            self.clock.set_speed(speed)
            return {"success": True, "action": "SET_SPEED", "speed": self.clock.speed_multiplier}

        elif action_type == "SELECT_NATION":
            nation_id = action.get("nation_id")
            if nation_id not in self.world.nations:
                return {"success": False, "error": "Nation nicht gefunden."}
            if account_id:
                self.world.active_players[account_id] = nation_id
                self.world.nations[nation_id]["player_account_id"] = account_id
            return {"success": True, "nation_id": nation_id}

        elif action_type == "BUILD":
            province_id = action.get("province_id")
            building_type = action.get("building_type")
            nation_id = action.get("nation_id")
            return self.world.build_in_province(province_id, building_type, nation_id)

        return {"success": False, "error": f"Unbekannte Aktion '{action_type}'"}

# Singleton engine instance
engine = SimulationEngine()
