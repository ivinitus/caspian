from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from sqlalchemy import select

from app.api.auth import router as auth_router
from app.api.conversation import router as conversation_router
from app.api.llm import router as llm_router
from app.api.plugins import router as plugins_router
from app.api.preferences import router as preferences_router
from app.api.ws import router as ws_router
from app.core.config import settings
from app.db.models import SessionLocal
from app.db.models import User
from app.db.models import init_db
from app.discord_bot.runner import start_discord_bot

app = FastAPI(title=settings.app_name)

# CORS for cross-platform clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(conversation_router)
app.include_router(llm_router)
app.include_router(plugins_router)
app.include_router(preferences_router)
app.include_router(ws_router)


@app.on_event("startup")
async def startup_event():
    # Ensure DB schema exists
    await init_db()
    # Optionally seed a default user for personal use
    if settings.create_default_user_on_startup:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        async with SessionLocal() as db:
            result = await db.execute(
                select(User).where(
                    User.username == settings.default_username
                )
            )
            user = result.scalar_one_or_none()
            if not user:
                hashed_pw = pwd_context.hash(settings.default_user_password)
                db.add(User(username=settings.default_username, hashed_password=hashed_pw))
                await db.commit()
    start_discord_bot()


@app.get("/")
def read_root():
    return {"message": "Hello Sir, I am Caspian. How may I assist you today?"}
