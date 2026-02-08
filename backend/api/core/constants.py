# Similarity thresholds
KB_GAP_THRESHOLD = 0.85  # Below this = gap detected

# Search defaults
SEARCH_RESULT_LIMIT = 5  # Default top-k results
CONTENT_PREVIEW_LENGTH = 500  # Chars to show in previews

# Pagination
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Hybrid search
HYBRID_SEARCH_OVERFETCH = 20  # Overfetch for semantic + FTS before merging
RRF_K = 60  # Reciprocal Rank Fusion constant (higher = less top-heavy)
SEMANTIC_WEIGHT = 0.7  # Weight for semantic results in RRF
FTS_WEIGHT = 0.3  # Weight for full-text search results in RRF

# Reranking
ENABLE_RERANKING = True
RERANK_CANDIDATE_COUNT = 15  # Number of candidates to send to LLM for reranking

# Embedding config
EMBEDDING_TEXT_SEPARATOR = "\n"  # Separator for title+body concatenation
