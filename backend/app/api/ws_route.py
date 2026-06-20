# backend/app/api/ws_route.py
"""WebSocket endpoint — browsers connect here for live updates."""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websockets.manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint. Browser connects once and stays connected.
    Server pushes messages when sensor data, alerts, or simulation results arrive.

    Message types the browser receives:
      - sensor_update:        a sensor published a new reading
      - alert:                an alert threshold was breached
      - monte_carlo_complete: a background simulation finished
      - connected:            initial connection confirmation

    Connect from JavaScript:
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onmessage = (event) => { const msg = JSON.parse(event.data); };
    """
    await ws_manager.connect(websocket)

    await ws_manager.send_to(websocket, json.dumps({
        "type": "connected",
        "message": "Connected to SupplyChain-Twin live feed",
        "active_connections": ws_manager.connection_count,
    }))

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type")

                if msg_type == "ping":
                    await ws_manager.send_to(websocket, json.dumps({"type": "pong"}))
                elif msg_type == "subscribe_node":
                    node_id = msg.get("node_id")
                    await ws_manager.send_to(websocket, json.dumps({
                        "type": "subscribed", "node_id": node_id,
                    }))
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
