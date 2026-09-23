from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from app.core.config import settings
from rank_bm25 import BM25Okapi
import numpy as np
from typing import List, Dict, Any

class HybridVectorStore:
    """
    Hybrid search combining dense (semantic) and sparse (BM25) retrieval
    for improved accuracy and robustness.
    """
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small", 
            openai_api_key=settings.OPENAI_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        self.dense_store = Chroma(
            collection_name="rag_documents",
            embedding_function=self.embeddings,
            persist_directory=settings.CHROMA_PERSIST_DIR
        )
        self.bm25_index = None
        self.documents = []
        self._initialize_bm25()
    
    def _initialize_bm25(self):
        """Initialize BM25 index with existing documents."""
        try:
            # Get all documents from ChromaDB
            all_docs = self.dense_store._collection.get()
            if all_docs and all_docs['documents']:
                self.documents = all_docs['documents']
                # Tokenize documents for BM25
                tokenized_docs = [doc.split() for doc in self.documents]
                self.bm25_index = BM25Okapi(tokenized_docs)
        except Exception as e:
            print(f"BM25 initialization error: {e}")
    
    def add_documents(self, documents: List[Any]):
        """Add documents to both dense and sparse stores."""
        # Add to ChromaDB (dense)
        self.dense_store.add_documents(documents=documents)
        
        # Update BM25 index with document content
        for doc in documents:
            self.documents.append(doc.page_content)
        
        # Rebuild BM25 index
        if self.documents:
            tokenized_docs = [doc.split() for doc in self.documents]
            self.bm25_index = BM25Okapi(tokenized_docs)
    
    def hybrid_search(self, query: str, k: int = 5, alpha: float = 0.5) -> List[Dict]:
        """
        Perform hybrid search combining dense and sparse results.
        Simplified approach: primarily use dense search, supplement with BM25.
        
        Args:
            query: Search query
            k: Number of results to return
            alpha: Weight for dense search (0-1), higher = more semantic
            
        Returns:
            List of documents
        """
        # Dense search (semantic) - primary method
        dense_results = self.dense_store.similarity_search_with_score(query, k=k)
        
        # If we have BM25, supplement with sparse results
        if self.bm25_index and len(dense_results) < k:
            tokenized_query = query.split()
            sparse_results = self.bm25_index.get_top_n(tokenized_query, self.documents, n=k)
            
            # Add sparse results that aren't already in dense results
            dense_contents = {doc[0].page_content for doc in dense_results}
            for sparse_doc in sparse_results:
                if len(dense_results) >= k:
                    break
                if sparse_doc not in dense_contents:
                    from langchain.schema import Document
                    dense_results.append((Document(page_content=sparse_doc, metadata={"source": "bm25"}), 1.0))
        
        # Return just the documents (without scores)
        return [doc for doc, score in dense_results[:k]]
    
    def as_retriever(self, search_type: str = "hybrid", **kwargs):
        """Return retriever with specified search type."""
        if search_type == "hybrid":
            return HybridRetriever(self, **kwargs)
        else:
            return self.dense_store.as_retriever(search_type=search_type, **kwargs)


class HybridRetriever:
    """Custom retriever for hybrid search."""
    
    def __init__(self, store: HybridVectorStore, **kwargs):
        self.store = store
        self.kwargs = kwargs
    
    def invoke(self, query: str) -> List[Any]:
        k = self.kwargs.get('k', 5)
        alpha = self.kwargs.get('alpha', 0.5)
        return self.store.hybrid_search(query, k=k, alpha=alpha)


def get_hybrid_vector_store() -> HybridVectorStore:
    """Get singleton instance of hybrid vector store."""
    if not hasattr(get_hybrid_vector_store, 'instance'):
        get_hybrid_vector_store.instance = HybridVectorStore()
    return get_hybrid_vector_store.instance