from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from sqlalchemy import select
import asyncio

from app.api.auth import router as auth_router
from app.api.conversation import router as conversation_router
from app.api.llm import router as llm_router
from app.api.plugins import router as plugins_router
from app.api.preferences import router as preferences_router
from app.api.ws import router as ws_router
from app.api.reminders import router as reminders_router
from app.core.config import settings
from app.db.models import SessionLocal, User, init_db
from app.discord_bot.runner import start_discord_bot
from app.reminders import check_reminders_periodically
import uvicorn
from app.api.rag import router as rag_router

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag_router)
app.include_router(auth_router)
app.include_router(conversation_router)
app.include_router(llm_router)
app.include_router(plugins_router)
app.include_router(preferences_router)
app.include_router(ws_router)
app.include_router(reminders_router)

@app.on_event("startup")
async def startup_event():
    main_loop = asyncio.get_running_loop()
    await init_db()
    
    # Check if vector extension is available
    try:
        async with SessionLocal() as db:
            await db.execute("SELECT '[1,2,3]'::vector")
            print("Vector extension is available and working properly")
    except Exception as e:
        print(f"ERROR: Vector extension is not available: {e}")
        print("Please make sure PostgreSQL vector extension is installed")

    # Start Discord bot only if token is set
    if settings.discord_token:
        try:
            start_discord_bot(main_loop)
        except Exception as e:
            print(f"Warning: Failed to start Discord bot: {e}")
            print("Continuing without Discord bot...")
    else:
        print("DISCORD_TOKEN not set; Discord bot will not start.")

    # Start the reminder checking task
    try:
        asyncio.create_task(check_reminders_periodically())
        print("Reminder checking task started")
    except Exception as e:
        print(f"Warning: Failed to start reminder checking task: {e}")

    if settings.create_default_user_on_startup:
        if not settings.default_user_password:
            raise RuntimeError("DEFAULT_USER_PASSWORD is not set or is empty. Please set it in your environment or .env file.")
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        async with SessionLocal() as db:
            result = await db.execute(
                select(User).where(User.username == settings.default_username)
            )
            user = result.scalar_one_or_none()
            if not user:
                hashed_pw = pwd_context.hash(settings.default_user_password)
                db.add(User(username=settings.default_username, hashed_password=hashed_pw))
                await db.commit()


@app.get("/")
def read_root():
    return {"message": "Hello Sir"}

@app.get("/health")
async def health_check():
    try:
        async with SessionLocal() as db:
            await db.execute("SELECT '[1,2,3]'::vector")
        return {"status": "healthy", "vector_extension": "available"}
    except Exception as e:
        return {"status": "unhealthy", "vector_extension": "unavailable", "error": str(e)}

@app.get("/api/health")
def api_health_check():
    return {"status": "API is healthy"}
