"""Constants and configuration for RAG system."""

# Embedding configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Chunking configuration
MAX_CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# Search configuration
DEFAULT_SEARCH_LIMIT = 5
MIN_RELEVANCE_SCORE = 0.3
SEMANTIC_WEIGHT = 0.7
LEXICAL_WEIGHT = 0.3

# Error handling
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
