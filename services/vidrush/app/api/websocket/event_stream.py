import asyncio
import json
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_client_connected", clients=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("websocket_client_disconnected", clients=len(self.active_connections))

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead_connections.append(connection)
                
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

# Global event bridge from EventBus to WebSocket
async def bridge_events_to_ws(event: dict):
    # Only forward safe events to frontend
    allowed_types = {
        "WORKFLOW_STARTED", "HOOK_READY", "SCRIPT_READY", 
        "VOICE_READY", "SUBTITLES_READY", "VISUALS_READY", 
        "RENDER_PROGRESS", "WORKFLOW_COMPLETED", "WORKFLOW_FAILED",
        "GPU_WARNING"
    }
    if event["type"] in allowed_types:
        await manager.broadcast(event)

# Subscribe the WebSocket bridge to the EventBus globally
# We map a wildcard-like pattern by subscribing to each explicitly or having the bus support it.
# For now, we will subscribe to the allowed types:
for event_type in ["WORKFLOW_STARTED", "HOOK_READY", "SCRIPT_READY", "VOICE_READY", "SUBTITLES_READY", "VISUALS_READY", "RENDER_PROGRESS", "WORKFLOW_COMPLETED", "WORKFLOW_FAILED", "GPU_WARNING"]:
    event_bus.subscribe(event_type, bridge_events_to_ws)


@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for ping/pong if necessary
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        manager.disconnect(websocket)
