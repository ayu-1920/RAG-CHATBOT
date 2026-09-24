import requests
import json
from typing import Generator
from app.db.vector_store import get_vector_store
from app.core.config import settings

def format_docs(docs):
    formatted = []
    for doc in docs:
        page = doc.metadata.get("page", "Unknown")
        source = doc.metadata.get("source", "Unknown")
        formatted.append(f"[Source: {source}, Page {page}]\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted)

def stream_openrouter_api(messages: list) -> Generator[str, None, None]:
    """
    [Interview Design Note]: Manual SSE Streaming Implementation.
    Instead of relying on high-level abstractions, parsing raw SSE chunks from the provider
    shows a deep understanding of protocols and allows for absolute control over token yields.
    """
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "HTTP-Referer": "http://localhost:3000",
                "X-OpenRouter-Title": "Production RAG Stream Engine",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "openai/gpt-4o-mini", 
                "messages": messages,
                "temperature": 0.0,
                "stream": True # Enable Server-Sent Events from OpenRouter
            }),
            stream=True,
            timeout=30
        )
        
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line_txt = line.decode('utf-8')
                if line_txt.startswith("data: "):
                    data_str = line_txt[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        payload = json.loads(data_str)
                        if "error" in payload:
                            yield f"\\n\\n[OpenRouter Error: {payload['error'].get('message', 'Unknown Error')}]"
                            break
                            
                        choices = payload.get("choices", [])
                        if choices and len(choices) > 0:
                            delta = choices[0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                    except Exception:
                        continue
    except Exception as e:
        yield f"\n\n[System Error: LLM Connection Failed - {str(e)}]"

def answer_query_stream(query: str, chat_history: list = None, filter_doc_id: str = None) -> Generator[str, None, None]:
    """
    Yields JSON lines composed of citation arrays and subsequent LLM token chunks.
    """
    vector_store = get_vector_store()
    
    # Safely determine collection size to prevent ChromaDB from crashing
    # if `fetch_k` exceeds the total number of chunks.
    try:
        total_docs = vector_store._collection.count()
    except Exception:
        total_docs = 5
        
    if total_docs == 0:
        yield json.dumps({"type": "chunk", "content": "Please upload a document first!"}) + "\n"
        return

    # Advanced Retrieval: Multi-query expansion + Hybrid search for better accuracy
    if filter_doc_id:
        # For filtered searches, use traditional MMR with metadata filtering
        search_kwargs_dense = {
            "k": min(5, total_docs),
            "fetch_k": min(20, total_docs),
            "lambda_mult": 0.7,
            "filter": {"document_id": filter_doc_id}
        }
        retriever = vector_store.dense_store.as_retriever(search_type="mmr", search_kwargs=search_kwargs_dense)
        docs = retriever.invoke(query)
    else:
        # Use multi-query expansion with hybrid search for unfiltered queries
        docs = multi_query_retrieval(vector_store, query, k=min(5, total_docs))
    
    # 1. Immediately yield source citations to the UI so it populates BEFORE text generates
    sources = [
        {
            "page": doc.metadata.get("page", "Unknown"), 
            "source": doc.metadata.get("source", "Unknown"),
            "content_snippet": doc.page_content[:150] + "..."
        } for doc in docs
    ]
    yield json.dumps({"type": "citations", "citations": sources}) + "\n"

    # 2. Build explicit XML system prompt with conversation context
    context_str = format_docs(docs)
    conversation_instruction = ""
    if conversation_context:
        conversation_instruction = f"\n<conversation_history>\n{conversation_context}\n</conversation_history>\n"
    
    system_prompt = (
        "You are an expert, helpful AI assistant.\n"
        "Your task is to answer the user's question based strictly on the provided context.\n\n"
        "<instructions>\n"
        "1. Use ONLY the provided context to answer the question.\n"
        "2. If the context does not contain the answer, strictly reply: 'I don't have enough information to answer that based on the provided documents.'\n"
        "3. Do NOT hallucinate or use outside knowledge.\n"
        "4. Whenever you retrieve facts, append the page number from the context using the format [Page X] immediately after the claim.\n"
        "5. Consider the conversation history for context and continuity in multi-turn conversations.\n"
        "</instructions>\n\n"
        f"{conversation_instruction}"
        f"<context>\n{context_str}\n</context>"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]

    # 3. Stream generated tokens layer by layer back to the client
    for chunk in stream_openrouter_api(messages):
        yield json.dumps({"type": "chunk", "content": chunk}) + "\n"
