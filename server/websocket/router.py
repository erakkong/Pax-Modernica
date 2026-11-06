"""
Pax Modernica - WebSocket Router
Provides real-time duplex channel for game clock, province inspection, and player commands.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from server.websocket.connection_manager import manager
from server.simulation.engine import engine
import logging

logger = logging.getLogger("pax_ws_router")
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send full initial game state on connection
        init_payload = {
            "type": "INIT_STATE",
            "clock": engine.clock.to_dict(),
            "world": engine.world.to_dict()
        }
        await manager.send_personal(websocket, init_payload)

        # Message loop
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "PING":
                await manager.send_personal(websocket, {"type": "PONG"})
                continue

            # Process action via simulation engine
            result = engine.process_action(data)

            if result.get("success"):
                # Broadcast changes to all players (e.g. speed change, building, pause)
                broadcast_msg = {
                    "type": "ACTION_UPDATE",
                    "action": data,
                    "result": result,
                    "clock": engine.clock.to_dict()
                }
                # If building, include updated province and nation data
                if data.get("type") == "BUILD":
                    pid = data.get("province_id")
                    nid = data.get("nation_id")
                    broadcast_msg["updated_province"] = engine.world.provinces.get(pid)
                    broadcast_msg["updated_nation"] = engine.world.nations.get(nid)

                await manager.broadcast(broadcast_msg)
            else:
                await manager.send_personal(websocket, {
                    "type": "ACTION_ERROR",
                    "error": result.get("error", "Aktion fehlgeschlagen")
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket Fehler: {e}", exc_info=True)
        manager.disconnect(websocket)
