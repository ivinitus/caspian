from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from app.db.models import Reminder, User, SessionLocal
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/reminders", tags=["reminders"])

class ReminderCreate(BaseModel):
    content: str
    remind_at: datetime

@router.post("/", status_code=201)
async def create_reminder(
    reminder_data: ReminderCreate,
    current_user: User = Depends(get_current_user)
):
    async with SessionLocal() as db:
        new_reminder = Reminder(
            user_id=current_user.id,
            content=reminder_data.content,
            remind_at=reminder_data.remind_at,
        )
        db.add(new_reminder)
        await db.commit()
        return {"msg": "Reminder has been set, Sir."}