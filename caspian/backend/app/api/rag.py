from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.models import Document, SessionLocal, User
from app.rag import get_embedding

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    try:
        content = (await file.read()).decode("utf-8")
        # Simple chunking by paragraph
        chunks = [p.strip() for p in content.split("\n\n") if p.strip()]

        async with SessionLocal() as db:
            for chunk in chunks:
                embedding = get_embedding(chunk)
                doc = Document(
                    user_id=current_user.id, content=chunk, embedding=embedding
                )
                db.add(doc)
            await db.commit()

        return {"filename": file.filename, "chunks_added": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e