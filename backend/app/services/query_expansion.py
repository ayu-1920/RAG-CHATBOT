import requests
import json
from typing import List
from app.core.config import settings

def expand_query_with_llm(query: str) -> List[str]:
    """
    Use LLM to generate expanded queries for better retrieval.
    This helps find relevant content that might not match the original query exactly.
    """
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "HTTP-Referer": "http://localhost:3000",
                "X-OpenRouter-Title": "RAG Query Expansion",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": """You are a query expansion expert. Your task is to generate 3-5 alternative search queries based on the user's original question.
                        
Rules:
1. Generate queries that are semantically related but use different wording
2. Include technical terms, synonyms, and related concepts
3. Focus on different aspects of the question
4. Return ONLY a JSON array of query strings, no other text
5. Each query should be self-contained and searchable

Example:
Input: "How do I create a table in MySQL?"
Output: ["MySQL CREATE TABLE syntax", "database table creation commands", "MySQL table structure definition", "how to define columns in MySQL"]"""
                    },
                    {
                        "role": "user", 
                        "content": f"Generate expanded queries for: {query}"
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 200
            }),
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract expanded queries from response
        content = result['choices'][0]['message']['content'].strip()
        
        # Try to parse as JSON array
        try:
            expanded_queries = json.loads(content)
            if isinstance(expanded_queries, list):
                return [query] + expanded_queries  # Include original query
        except json.JSONDecodeError:
            # Fallback: split by newlines if not JSON
            expanded_queries = [line.strip().strip('"').strip("'") 
                               for line in content.split('\n') 
                               if line.strip()]
            return [query] + expanded_queries if expanded_queries else [query]
        
        return [query]
        
    except Exception as e:
        print(f"Query expansion error: {e}")
        return [query]  # Fallback to original query


def multi_query_retrieval(vector_store, query: str, k: int = 5) -> List:
    """
    Perform retrieval using multiple expanded queries and merge results.
    This improves recall by finding documents that match different query formulations.
    """
    expanded_queries = expand_query_with_llm(query)
    
    all_results = []
    seen_ids = set()
    
    for expanded_query in expanded_queries[:3]:  # Limit to top 3 expanded queries
        try:
            results = vector_store.hybrid_search(expanded_query, k=k*2)
            for doc in results:
                doc_id = doc.metadata.get('id', tuple(doc.metadata.values()))
                if doc_id not in seen_ids:
                    all_results.append(doc)
                    seen_ids.add(doc_id)
                    if len(all_results) >= k:
                        break
        except Exception as e:
            print(f"Error with query '{expanded_query}': {e}")
            continue
    
    # If we didn't get enough results, fall back to original query
    if len(all_results) < k:
        try:
            fallback_results = vector_store.hybrid_search(query, k=k)
            for doc in fallback_results:
                doc_id = doc.metadata.get('id', tuple(doc.metadata.values()))
                if doc_id not in seen_ids:
                    all_results.append(doc)
                    seen_ids.add(doc_id)
        except Exception as e:
            print(f"Fallback retrieval error: {e}")
    
    return all_results[:k]