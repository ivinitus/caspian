from typing import Dict, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer

from .short_term import ShortTermMemory
from .long_term import LongTermMemory

class MemoryManager:
    def __init__(self, model: SentenceTransformer = None):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(model)
    
    async def add_interaction(self, db: AsyncSession, user_id: int, message: dict):
        """Add new interaction to both memories if relevant"""
        # Always add to short-term memory
        self.short_term.add(message)
        
        # Store important information in long-term memory
        if self._is_important(message):
            await self.long_term.store(
                db=db,
                user_id=user_id,
                content=message["content"],
                metadata={
                    "type": message.get("type", "general"),
                    "importance": self._calculate_importance(message)
                }
            )
    
    async def get_relevant_context(
        self, 
        db: AsyncSession, 
        user_id: int, 
        query: str,
        st_limit: int = 5,
        lt_limit: int = 3
    ) -> Dict[str, List]:
        """Get context from both memories"""
        return {
            "short_term": self.short_term.get_context(k=st_limit),
            "long_term": await self.long_term.retrieve(db, user_id, query, k=lt_limit)
        }
    
    def _is_important(self, message: dict) -> bool:
        """Determine if message should be stored in long-term memory"""
        importance_score = self._calculate_importance(message)
        return importance_score >= 0.7  # Threshold for importance
    
    def _calculate_importance(self, message: dict) -> float:
        """Calculate importance score of a message"""
        # Simple heuristic based on message length
        content = message.get("content", "")
        if not content:
            return 0.0
            
        # Simple length-based importance (longer messages might be more important)
        base_score = min(len(content.split()) / 100, 1.0)
        
        # Boost score for certain message types
        type_boost = {
            "question": 0.2,
            "answer": 0.3,
            "fact": 0.4,
            "command": 0.2
        }.get(message.get("type", "general"), 0.0)
        
        return min(base_score + type_boost, 1.0)
