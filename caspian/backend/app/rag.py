from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document

model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embedding(text: str) -> list[float]:
    return model.encode(text).tolist()


async def get_similar_documents(
    db: AsyncSession, user_id: int, query: str, limit: int = 5
) -> list[Document]:
    embedding = get_embedding(query)
    result = await db.execute(
        select(Document)
        .order_by(Document.embedding.l2_distance(embedding))
        .limit(limit)
    )
    return result.scalars().all()