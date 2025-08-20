"""Utility functions for text processing and chunking."""
import re
from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import sent_tokenize

def preprocess_text(text: str) -> str:
    """Clean and preprocess text for better embedding."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text

def smart_chunk_text(text: str, max_chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Intelligently chunk text while preserving sentence boundaries and context.
    
    Args:
        text: Input text to chunk
        max_chunk_size: Maximum chunk size in characters
        overlap: Number of words to overlap between chunks
    
    Returns:
        List of text chunks
    """
    # First split into sentences
    sentences = sent_tokenize(text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        
        if current_length + sentence_length <= max_chunk_size:
            current_chunk.append(sentence)
            current_length += sentence_length
        else:
            # Add current chunk to chunks list
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            
            # Start new chunk with overlap
            if current_chunk and len(current_chunk) > 1:
                # Add last sentence from previous chunk for context
                current_chunk = [current_chunk[-1], sentence]
                current_length = len(current_chunk[-1]) + sentence_length
            else:
                current_chunk = [sentence]
                current_length = sentence_length
    
    # Add final chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def calculate_relevance_score(query: str, text: str, embedding_similarity: float) -> float:
    """
    Calculate relevance score using both semantic and lexical similarity.
    
    Args:
        query: Search query
        text: Text to compare against
        embedding_similarity: Cosine similarity from embeddings
    
    Returns:
        Combined relevance score
    """
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([query, text])
        lexical_similarity = (tfidf_matrix * tfidf_matrix.T).A[0, 1]
    except:
        lexical_similarity = 0.0
    
    # Combine scores (weighted average)
    semantic_weight = 0.7
    lexical_weight = 0.3
    
    return (semantic_weight * embedding_similarity) + (lexical_weight * lexical_similarity)

def rerank_results(query: str, texts: List[str], scores: List[float]) -> List[tuple[str, float]]:
    """
    Rerank results based on relevance scores.
    
    Args:
        query: Original search query
        texts: List of text results
        scores: Initial similarity scores
    
    Returns:
        List of (text, score) tuples, reranked by relevance
    """
    # Calculate final scores
    final_scores = []
    for text, embedding_score in zip(texts, scores):
        relevance_score = calculate_relevance_score(query, text, embedding_score)
        final_scores.append(relevance_score)
    
    # Create (text, score) pairs and sort by score
    results = list(zip(texts, final_scores))
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results
