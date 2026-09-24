from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.db.vector_store import get_vector_store
from app.core.config import settings
import aiofiles
import os

async def process_and_store_pdf(file: UploadFile, document_id: str):
    """
    Background task to process PDFs. 
    1. Saves file temporarily.
    2. Loads and parses PDF.
    3. Splits into semantically meaningful chunks with overlap.
    4. Upserts to ChromaDB with metadata.
    """
    temp_path = f"app/temp_{file.filename}"
    
    # Asynchronous file writing to prevent blocking the event loop
    async with aiofiles.open(temp_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    try:
        # 1. Load Document
        loader = PyPDFLoader(temp_path)
        docs = loader.load()

        # 2. Add source metadata for filtering/citations later
        for doc in docs:
            doc.metadata["document_id"] = document_id
            doc.metadata["source"] = file.filename

        # 3. Smart Chunking: Recursive keeps sentences/paragraphs intact
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", " ", ""],
            add_start_index=True # Crucial for accurate UI citations
        )
        splits = text_splitter.split_documents(docs)

        # 4. Store in Vector DB
        vector_store = get_vector_store()
        vector_store.add_documents(documents=splits)
        
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
