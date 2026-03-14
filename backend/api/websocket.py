import asyncio
import json
from datetime import datetime
from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])

# Global broadcaster — simple in-process pub/sub
_connections: list[WebSocket] = []


async def broadcast(event: dict[str, Any]) -> None:
    """Send a JSON event to all connected WebSocket clients."""
    payload = json.dumps({**event, "timestamp": datetime.utcnow().isoformat()})
    dead: list[WebSocket] = []
    for ws in _connections:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _connections.remove(ws)


@router.websocket("/ws/activity")
async def activity_feed(websocket: WebSocket):
    await websocket.accept()
    _connections.append(websocket)
    try:
        # Keep connection alive — send heartbeat every 30s
        while True:
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "heartbeat"}))
    except Exception:
        pass
    finally:
        if websocket in _connections:
            _connections.remove(websocket)
