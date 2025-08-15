from datetime import datetime

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.db.models import SessionLocal
from app.db.models import User

router = APIRouter(prefix="/admin", tags=["admin"])


class UserRead(BaseModel):
    id: int
    username: str
    created_at: datetime


@router.get("/users", response_model=list[UserRead])
async def list_users():
    async with SessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        return [UserRead(id=u.id, username=u.username, created_at=u.created_at) for u in users]


@router.delete("/users/{user_id}")
async def delete_user(user_id: int):
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await db.delete(user)
        await db.commit()
        return {"msg": "User deleted"}
