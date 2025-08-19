from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Document, SessionLocal, User
from app.rag import get_embedding

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
):
    async with SessionLocal() as db:
        try:
            content = (await file.read()).decode("utf-8")
            chunks = [p.strip() for p in content.split("\n\n") if p.strip()]

            for chunk in chunks:
                embedding = get_embedding(chunk)
                doc = Document(
                    content=chunk, embedding=embedding
                )
                db.add(doc)
            await db.commit()

            return {"filename": file.filename, "chunks_added": len(chunks)}
        except Exception as e:
            await db.rollback()
            print(f"Error in upload_document: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e