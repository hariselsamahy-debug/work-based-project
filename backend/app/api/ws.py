from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/alerts")
async def alerts(ws: WebSocket):
    hub = ws.app.state.hub
    await hub.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keeps the connection open; clients don't send anything
    except WebSocketDisconnect:
        hub.disconnect(ws)
