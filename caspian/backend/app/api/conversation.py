from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Conversation, Message, SessionLocal, User
from pydantic import BaseModel
from typing import List
import datetime

router = APIRouter(prefix="/conversations", tags=["conversations"])

class MessageCreate(BaseModel):
    content: str
    sender: str  # 'user' or 'caspian'

class MessageRead(BaseModel):
    id: int
    content: str
    sender: str
    timestamp: datetime.datetime

class ConversationRead(BaseModel):
    id: int
    started_at: datetime.datetime
    messages: List[MessageRead] = []

@router.post("/", response_model=ConversationRead)
async def start_conversation(user_id: int):
    async with SessionLocal() as db:
        conv = Conversation(user_id=user_id)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        return ConversationRead(id=conv.id, started_at=conv.started_at, messages=[])

@router.get("/{conversation_id}/messages", response_model=List[MessageRead])
async def get_messages(conversation_id: int):
    async with SessionLocal() as db:
        result = await db.execute(Message.__table__.select().where(Message.conversation_id == conversation_id))
        messages = result.fetchall()
        return [MessageRead(id=m.id, content=m.content, sender=m.sender, timestamp=m.timestamp) for m in messages]

@router.post("/{conversation_id}/messages", response_model=MessageRead)
async def add_message(conversation_id: int, msg: MessageCreate):
    async with SessionLocal() as db:
        message = Message(conversation_id=conversation_id, content=msg.content, sender=msg.sender)
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return MessageRead(id=message.id, content=message.content, sender=message.sender, timestamp=message.timestamp)
