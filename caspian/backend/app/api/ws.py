from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from app.core.time_utils import get_current_time, format_time

router = APIRouter(prefix="/ws", tags=["ws"])

TIME_QUERIES = [
    "time", "what is the time", "current time", "date", "what is the date", "current date",
    "time now", "date now", "what's the time", "tell me the time", "tell me the date"
]

def is_time_query(text: str) -> bool:
    text = text.lower().strip()
    return any(q in text for q in TIME_QUERIES)

@router.websocket("/chat")
async def websocket_chat(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            if is_time_query(data):
                now_chennai = get_current_time("Asia/Kolkata")
                formatted = format_time(now_chennai)
                await ws.send_text(f"Current time in Chennai: {formatted}")
            else:
                await ws.send_text(data)
    except WebSocketDisconnect:
        return