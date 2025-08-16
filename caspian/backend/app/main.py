from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.conversation import router as conversation_router
from app.api.llm import router as llm_router
from app.api.plugins import router as plugins_router
from app.api.preferences import router as preferences_router
from app.api.ws import router as ws_router
from app.core.config import settings
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
    start_discord_bot()


@app.get("/")
def read_root():
    return {"message": "Hello Sir, I am Caspian. How may I assist you today?"}
