from app.core.config import settings
from app.db.hybrid_vector_store import get_hybrid_vector_store

def get_vector_store():
    """
    Returns the hybrid vector store for improved retrieval accuracy.
    Combines dense (semantic) and sparse (BM25) search for better results.
    """
    return get_hybrid_vector_store()
