import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.db.models import User, SessionLocal

# Configuration
SECRET_KEY = "your-secret-key"  # Replace with a secure key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

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

from typing import Dict, Any

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime.datetime

    @classmethod
    def from_orm(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            username=user.username,
            created_at=user.created_at
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
                detail="Username already registered"
            )
        
        # Create new user
        hashed_pw = get_password_hash(user.password)
        new_user = User(username=user.username, hashed_password=hashed_pw)
        db.add(new_user)
        
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=400, 
                detail="Registration failed"
            )
            
        return {"msg": "Registration successful"}

# Authentication utilities
async def get_user(db: AsyncSession, username: str) -> User | None:
    """Retrieve a user by username from the database."""
    result = await db.execute(
        User.__table__.select().where(User.username == username)
    )
    return result.scalar_one_or_none()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

def create_access_token(
    data: dict, 
    expires_delta: datetime.timedelta | None = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (
        expires_delta or 
        datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Login endpoint
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    """Authenticate user and return JWT token."""
    async with SessionLocal() as db:
        # Verify credentials
        user = await get_user(db, form_data.username)
        if not user or not verify_password(
            form_data.password, 
            user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate token
        access_token = create_access_token(
            data={"sub": user.username}
        )
        return {"access_token": access_token, "token_type": "bearer"}
