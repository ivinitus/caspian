from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

router = APIRouter(prefix="/ws", tags=["ws"])


@router.websocket("/chat")
async def websocket_chat(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            # For now, echo back; can integrate streaming LLM later
            await ws.send_text(data)
    except WebSocketDisconnect:
        return