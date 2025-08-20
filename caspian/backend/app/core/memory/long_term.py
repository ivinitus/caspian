from typing import List, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Memory, Document
from sentence_transformers import SentenceTransformer

class LongTermMemory:
    def __init__(self, model: SentenceTransformer = None):
        self.model = model or SentenceTransformer("all-MiniLM-L6-v2")
    
    async def store(self, db: AsyncSession, user_id: int, content: str, metadata: Dict = None):
        """Store important information in long term memory"""
        if metadata is None:
            metadata = {}
            
        embedding = self.model.encode(content).tolist()
        
        memory = Memory(
            user_id=user_id,
            content=content,
            embedding=embedding,
            meta_info=metadata,
            created_at=datetime.now()
        )
        
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
        return memory
    
    async def retrieve(self, db: AsyncSession, user_id: int, query: str, k: int = 3) -> List[Dict]:
        """Retrieve relevant memories based on query"""
        embedding = self.model.encode(query).tolist()
        
        result = await db.execute(
            select(Memory)
            .where(Memory.user_id == user_id)
            .order_by(Memory.embedding.l2_distance(embedding))
            .limit(k)
        )
        
        return result.scalars().all()
