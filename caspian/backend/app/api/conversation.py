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


class StartConversationRequest(BaseModel):
    user_id: int | None = None
    username: str | None = None


@router.post("/", response_model=ConversationRead)
async def start_conversation(
    req: StartConversationRequest | None = None,
    user_id: int | None = None,
):
    async with SessionLocal() as db:
        effective_user_id: int | None = None
        if req and req.user_id:
            effective_user_id = req.user_id
        elif user_id:
            effective_user_id = user_id
        elif req and req.username:
            # Look up user by username
            result = await db.execute(
                select(User).where(User.username == req.username)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            effective_user_id = user.id
        else:
            raise HTTPException(status_code=400, detail="Provide user_id or username")

        conv = Conversation(user_id=effective_user_id)
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
