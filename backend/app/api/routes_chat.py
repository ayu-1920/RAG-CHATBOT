from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.services.retrieval_qa import answer_query_stream
from app.services.conversation_memory import conversation_memory
import uuid

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    chat_history: list = []
    document_id: Optional[str] = None  # Added for Document Metadata Filtering
    session_id: Optional[str] = None  # For conversation memory

@router.post("/chat")
async def chat_with_docs(request: ChatRequest):
    """
    [Interview Design Note]: Streaming Responses with Conversation Memory.
    Waiting for a complete LLM generation can take 10+ seconds. By returning a StreamingResponse 
    (Server-Sent Events), the Time To First Token (TTFT) drops to ~500ms, providing massively better UX.
    Now includes conversation memory for multi-turn context.
    """
    try:
        # Generate or use session ID for conversation memory
        session_id = request.session_id or str(uuid.uuid4())
        
        # Add user message to conversation memory
        conversation_memory.add_message(session_id, "user", request.query)
        
        # Get conversation context for better retrieval
        conversation_context = conversation_memory.get_recent_context(session_id)
        
        # Stream response with conversation context
        response_stream = answer_query_stream(
            request.query, 
            request.chat_history, 
            request.document_id,
            session_id,
            conversation_context
        )
        
        return StreamingResponse(
            response_stream,
            media_type="application/x-ndjson"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
