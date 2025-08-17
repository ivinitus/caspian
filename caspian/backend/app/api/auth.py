from datetime import datetime
from datetime import timedelta

from fastapi import APIRouter
from fastapi import Body
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.db.models import SessionLocal
from app.db.models import User
from pydantic import ConfigDict
from sqlalchemy import select

# FastAPI router setup
router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# Pydantic models for request/response
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    created_at: datetime

    @classmethod
    def from_orm(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            username=user.username,
            created_at=user.created_at,
        )


# Auth endpoints
@router.post("/register", status_code=201)
async def register_user(user: UserCreate = Body(...)):
    """Register a new user with username and password."""
    async with SessionLocal() as db:
        # Check if user exists
        existing = await db.execute(
            User.__table__.select().where(User.username == user.username)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Username already registered",
            )

        # Create new user
        hashed_pw = get_password_hash(user.password)
        new_user = User(username=user.username, hashed_password=hashed_pw)
        db.add(new_user)

        try:
            await db.commit()
        except IntegrityError as err:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Registration failed",
            ) from err

        return {"msg": "Registration successful"}


# Authentication utilities
async def get_user(db, username: str) -> User | None:
    """Retrieve a user by username from the database."""
    # This is the corrected query
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()



def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


# Login endpoint
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """Authenticate user and return JWT token."""
    async with SessionLocal() as db:
        # Verify credentials
        user = await get_user(db, form_data.username)
        if not user or not verify_password(
            form_data.password,
            user.hashed_password,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate token
        access_token = create_access_token(data={"sub": user.username})
        return Token(access_token=access_token, token_type="bearer")
    

@router.post("/token/from-username")
async def get_token_from_username(username_data: dict):
    """Generate a token for a username without a password (for development)."""
    username = username_data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Username not provided")

    async with SessionLocal() as db:
        user = await get_user(db, username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        access_token = create_access_token(data={"sub": user.username})
        return Token(access_token=access_token, token_type="bearer")
