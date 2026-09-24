from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from app.core.config import settings

def get_vector_store() -> Chroma:
    """
    Initializes and returns the ChromaDB vector store instance.
    Uses text-embedding-3-small for cost-efficiency and high performance.
    """
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small", 
        openai_api_key=settings.OPENAI_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )
    
    return Chroma(
        collection_name="rag_documents",
        embedding_function=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIR
    )
