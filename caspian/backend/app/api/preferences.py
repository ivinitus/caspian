from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.db.models import SessionLocal
from app.db.models import User

router = APIRouter(prefix="/preferences", tags=["preferences"])


class PreferencesUpdate(BaseModel):
    preferences: dict


@router.get("/{user_id}")
async def get_preferences(user_id: int):
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"preferences": user.preferences or {}}


@router.put("/{user_id}")
async def set_preferences(user_id: int, body: PreferencesUpdate):
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.preferences = body.preferences
        await db.commit()
        return {"ok": True}