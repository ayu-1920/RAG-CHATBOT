# Production RAG Pipeline

This codebase demonstrates a Senior-level, enterprise-grade architecture for a Retrieval Augmented Generation system.

## Architectural Highlights to Mention in Interviews

### 1. Server-Sent Events (SSE) Streaming
- **The Problem:** LLMs take 5-15 seconds to generate full answers. Synchronous APIs cause HTTP timeouts and poor UX. Beginners typically wait for the entire string before returning a JSON object.
- **The Solution:** Implemented manual custom SSE parsing of the LLM provider's chunk stream inside a Python Generator (`retrieval_qa.py`), passing chunks dynamically through a FastAPI `StreamingResponse`. The Time-To-First-Token (TTFT) drops to milliseconds.
- **Citations-First Design:** The generator strictly yields the Document Citations as the absolute first chunk, allowing the frontend UI to instantly display source cards before the user even reads the text answer.

### 2. Advanced Retrieval Strategy (MMR)
- **The Problem:** Standard top-k cosine similarity often retrieves redundant chunks (e.g., 5 identical paragraphs representing the same concept), drastically limiting the LLM's world context.
- **The Solution:** Utilized Maximal Marginal Relevance (MMR) with a tuned `lambda_mult=0.7`. This finds 20 chunks but algorithmically returns the 5 most diverse yet relevant fragments.

### 3. Strict Context Isolation (Anti-Hallucination)
- **The Problem:** Prompt injection and LLM hallucination.
- **The Solution:** The system prompt securely isolates text fragments into strict `<context>` XML tags and specifically injects `[Source X, Page Y]` directly onto the payloads. The LLM is strongly instructed to reject requests operating outside that XML container, yielding absolute deterministic safety.

### 4. DevOps, Observability, and Clean Code
- **Containerization:** Wrote a non-root, multi-stage builder Dockerfile which caches compiled wheels for faster, highly deterministic deployments.
- **Centralized Logging:** Replaced scattered `print()` statements with a centralized `logger.py` module ready for Datadog or AWS Cloudwatch scraping.
- **Exception Handlers:** Added global FastAPI exception overrides in `main.py` that prevent massive stack traces from leaking to the frontend during 500 errors.
