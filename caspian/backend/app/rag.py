import asyncio
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import select, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
import nltk

from app.db.models import Document
from app.core.memory.memory_manager import MemoryManager
from app.core.text_utils import (
    preprocess_text,
    smart_chunk_text,
    calculate_relevance_score,
    rerank_results
)
from app.core.rag_config import (
    EMBEDDING_MODEL,
    MAX_CHUNK_SIZE,
    CHUNK_OVERLAP,
    DEFAULT_SEARCH_LIMIT,
    MIN_RELEVANCE_SCORE,
    MAX_RETRIES,
    RETRY_DELAY
)

nltk.download('punkt')

class RAGSystem:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.memory_manager = MemoryManager(self.model)

    async def process_document(self, content: str, metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Process a document for storage by chunking and embedding.
        
        Args:
            content: Document content
            metadata: Optional metadata about the document
            
        Returns:
            List of dictionaries containing chunks and their embeddings
        """
        # Preprocess text
        processed_text = preprocess_text(content)
        
        # Smart chunking
        chunks = smart_chunk_text(processed_text, MAX_CHUNK_SIZE, CHUNK_OVERLAP)
        
        # Generate embeddings for chunks
        chunk_data = []
        for chunk in chunks:
            embedding = self.get_embedding(chunk)
            chunk_data.append({
                "content": chunk,
                "embedding": embedding,
                "metadata": metadata or {}
            })
            
        return chunk_data

    def get_embedding(self, text: str) -> list[float]:
        """Get embedding with retries and error handling."""
        for attempt in range(MAX_RETRIES):
            try:
                processed_text = preprocess_text(text)
                return self.model.encode(processed_text).tolist()
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise Exception(f"Failed to generate embedding after {MAX_RETRIES} attempts: {e}")
                asyncio.sleep(RETRY_DELAY)

    async def get_similar_documents(
        self, 
        db: AsyncSession, 
        user_id: int, 
        query: str, 
        limit: int = DEFAULT_SEARCH_LIMIT
    ) -> dict:
        """
        Enhanced document retrieval with hybrid search and reranking.
        """
        # Preprocess query
        processed_query = preprocess_text(query)
        query_embedding = self.get_embedding(processed_query)
        
        # Hybrid search: combine semantic and keyword search
        result = await db.execute(
            select(Document)
            .where(
                or_(
                    Document.embedding.l2_distance(query_embedding) <= 1.0,  # Semantic similarity
                    Document.content.ilike(f"%{processed_query}%")  # Keyword match
                )
            )
            .order_by(Document.embedding.l2_distance(query_embedding))
            .limit(limit * 2)  # Get more results for reranking
        )
        documents = result.scalars().all()
        
        # Rerank results
        if documents:
            doc_texts = [doc.content for doc in documents]
            
            # Calculate cosine similarity manually using numpy
            def cosine_similarity(a, b):
                # Convert embedding to numpy array if it's a list
                if isinstance(a, list):
                    a = np.array(a)
                if isinstance(b, list):
                    b = np.array(b)
                
                # Calculate cosine similarity: dot(a, b) / (norm(a) * norm(b))
                return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            
            doc_scores = [
                1 - cosine_similarity(
                    query_embedding,
                    doc.embedding
                ) for doc in documents
            ]
            
            reranked = rerank_results(processed_query, doc_texts, doc_scores)
            
            # Filter by relevance score and limit
            filtered_docs = [
                doc for doc, score in zip(documents, [score for _, score in reranked])
                if score >= MIN_RELEVANCE_SCORE
            ][:limit]
        else:
            filtered_docs = []
        
        # Get memory context
        memories = await self.memory_manager.get_relevant_context(
            db=db,
            user_id=user_id,
            query=processed_query
        )
        
        return {
            "documents": filtered_docs,
            "memories": memories
        }

    async def add_to_memory(
        self,
        db: AsyncSession,
        user_id: int,
        message: dict
    ):
        """Add interaction to memory system"""
        await self.memory_manager.add_interaction(db, user_id, message)

# Initialize global RAG system
rag_system = RAGSystem()

# Backward compatibility functions
async def get_similar_documents(
    db: AsyncSession, 
    user_id: int, 
    query: str, 
    limit: int = 5
) -> list[Document]:
    """
    Backward compatibility wrapper for old get_similar_documents function.
    Returns only the documents list for compatibility with old code.
    """
    result = await rag_system.get_similar_documents(db, user_id, query, limit)
    return result["documents"]

def get_embedding(text: str) -> list[float]:
    """
    Backward compatibility wrapper for get_embedding function.
    """
    return rag_system.get_embedding(text)