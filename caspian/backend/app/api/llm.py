from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from app.core.llm import ask_gemini

router = APIRouter(prefix="/llm", tags=["llm"])


class LLMMessage(BaseModel):
	role: str  # 'user' or 'assistant'
	content: str


class LLMRequest(BaseModel):
	messages: list[LLMMessage]
	model: str = "gemini-1.5-flash"


@router.post("/chat")
async def chat_with_llm(req: LLMRequest):
	try:
		text = await ask_gemini([m.dict() for m in req.messages], model=req.model)
		return {"text": text}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e)) from None
