from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.services.retrieval_qa import answer_query_stream

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    chat_history: list = []
    document_id: Optional[str] = None  # Added for Document Metadata Filtering

@router.post("/chat")
async def chat_with_docs(request: ChatRequest):
    """
    [Interview Design Note]: Streaming Responses.
    Waiting for a complete LLM generation can take 10+ seconds. By returning a StreamingResponse 
    (Server-Sent Events), the Time To First Token (TTFT) drops to ~500ms, providing massively better UX.
    """
    try:
        return StreamingResponse(
            answer_query_stream(request.query, request.chat_history, request.document_id),
            media_type="application/x-ndjson"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
