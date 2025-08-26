from datetime import datetime

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.db.models import Conversation
from app.db.models import Message
from app.db.models import SessionLocal
from app.db.models import User

router = APIRouter(prefix="/conversations", tags=["conversations"])


class MessageCreate(BaseModel):
    content: str
    sender: str  # 'user' or 'caspian'


class MessageRead(BaseModel):
    id: int
    content: str
    sender: str
    timestamp: datetime


class ConversationRead(BaseModel):
    id: int
    started_at: datetime
    messages: list[MessageRead] = []


# Single-user mode: always use conversation_id=1
@router.post("/", response_model=ConversationRead)
async def start_conversation():
    async with SessionLocal() as db:
        conv = await db.get(Conversation, 1)
        if not conv:
            conv = Conversation(id=1)
            db.add(conv)
            await db.commit()
            await db.refresh(conv)
        return ConversationRead(id=conv.id, started_at=conv.started_at, messages=[])


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
async def get_messages(conversation_id: int):
    async with SessionLocal() as db:
        result = await db.execute(select(Message).where(Message.conversation_id == conversation_id))
        messages = result.scalars().all()
        return [
            MessageRead(
                id=m.id,
                content=m.content,
                sender=m.sender,
                timestamp=m.timestamp,
            )
            for m in messages
        ]


@router.post("/{conversation_id}/messages", response_model=MessageRead)
async def add_message(conversation_id: int, msg: MessageCreate):
    async with SessionLocal() as db:
        # First check if the conversation exists
        conv = await db.get(Conversation, conversation_id)
        
        # If not, create it (similar to your start_conversation endpoint)
        if not conv:
            conv = Conversation(id=conversation_id)
            db.add(conv)
            await db.flush()  # Flush to DB but don't commit yet
        
        # Now add the message
        message = Message(
            conversation_id=conversation_id,
            content=msg.content,
            sender=msg.sender,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return MessageRead(
            id=message.id,
            content=message.content,
            sender=message.sender,
            timestamp=message.timestamp,
        )
