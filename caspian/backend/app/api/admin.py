from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User, SessionLocal
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/admin", tags=["admin"])

class UserRead(BaseModel):
    id: int
    username: str
    created_at: str

@router.get("/users", response_model=List[UserRead])
async def list_users():
    async with SessionLocal() as db:
        result = await db.execute(User.__table__.select())
        users = result.fetchall()
        return [UserRead(id=u.id, username=u.username, created_at=str(u.created_at)) for u in users]

@router.delete("/users/{user_id}")
async def delete_user(user_id: int):
    async with SessionLocal() as db:
        result = await db.execute(User.__table__.select().where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await db.delete(user)
        await db.commit()
        return {"msg": "User deleted"}
