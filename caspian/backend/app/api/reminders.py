from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

from app.db.models import Reminder, SessionLocal

router = APIRouter(prefix="/reminders", tags=["reminders"])

class ReminderCreate(BaseModel):
    content: str
    remind_at: datetime

@router.post("/", status_code=201)
async def create_reminder(reminder_data: ReminderCreate):
    async with SessionLocal() as db:
        new_reminder = Reminder(
            content=reminder_data.content,
            remind_at=reminder_data.remind_at,
        )
        db.add(new_reminder)
        await db.commit()
        return {"msg": "Reminder has been set, Sir."}