from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from app.core.llm import ask_openai

router = APIRouter(prefix="/llm", tags=["llm"])


class LLMMessage(BaseModel):
	role: str  # 'user' or 'assistant'
	content: str


class LLMRequest(BaseModel):
	messages: list[LLMMessage]
	model: str = "gpt-3.5-turbo"


@router.post("/chat")
async def chat_with_llm(req: LLMRequest):
	try:
		response = await ask_openai([m.dict() for m in req.messages], model=req.model)
		return response
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e)) from None
