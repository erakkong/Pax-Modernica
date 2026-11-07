"""
Pax Modernica - Main Application Server
FastAPI web application, lifespan orchestrator, REST API, WebSockets & SPA hosting.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from server.database.connection import init_db, get_db
from server.auth.router import router as auth_router
from server.websocket.router import router as ws_router
from server.websocket.connection_manager import manager
from server.simulation.engine import engine

CLIENT_DIR = Path(__file__).resolve().parent.parent / "client"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database and start simulation loop
    await init_db()
    engine.broadcast_callback = manager.broadcast
    engine.start()
    yield
    # Shutdown: stop simulation loop
    engine.stop()

app = FastAPI(
    title="Pax Modernica API",
    description="Historische Grand-Strategy-Simulation 1700–1930",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(ws_router)

class SaveRequest(BaseModel):
    name: str = "Spielstand"

@app.post("/api/game/save")
async def save_game(req: SaveRequest):
    save_id = await engine.save_state(req.name)
    return {"status": "success", "save_id": save_id, "name": req.name}

@app.get("/api/game/saves")
async def list_saves():
    async with get_db() as db:
        async with db.execute(
            "SELECT id, name, game_year, game_month, game_day, tick_id, created_at, updated_at FROM game_saves ORDER BY updated_at DESC"
        ) as cur:
            rows = await cur.fetchall()
            saves = [dict(row) for row in rows]
            return {"saves": saves}

@app.post("/api/game/load/{save_id}")
async def load_game(save_id: str):
    success = await engine.load_state(save_id)
    if not success:
        raise HTTPException(status_code=404, detail="Spielstand nicht gefunden")
    # Broadcast full state update to clients
    await manager.broadcast({
        "type": "INIT_STATE",
        "clock": engine.clock.to_dict(),
        "world": engine.world.to_dict()
    })
    return {"status": "success", "loaded_year": engine.clock.year}

@app.get("/api/game/scenario")
async def get_scenario():
    return engine.world.scenario_meta

@app.get("/api/game/state")
async def get_game_state():
    return {
        "clock": engine.clock.to_dict(),
        "world": engine.world.to_dict(),
        "nations": engine.world.nations,
        "provinces": engine.world.provinces
    }

@app.get("/api/game/map")
async def get_map_data():
    map_file = Path(__file__).resolve().parent / "data" / "europe_map.json"
    if not map_file.exists():
        raise HTTPException(status_code=404, detail="Kartendaten nicht gefunden")
    return map_file.read_text(encoding="utf-8")

# Mount client static files
if CLIENT_DIR.exists():
    app.mount("/", StaticFiles(directory=str(CLIENT_DIR), html=True), name="client")
