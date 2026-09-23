import requests
import json
import time

API_URL = "http://localhost:8000/api/chat"

test_queries = [
    # 1. Broad factual query
    "What are the main topics discussed in the document?",
    # 2. Page-number expectation
    "Can you provide a specific fact and cite the exact page number it came from?",
    # 3. Known Hallucination test (Asking about something unlikely to be in the PDF)
    "What is the exact recipe for baking a chocolate cake?",
]

def run_eval_queries():
    print("--- 🚀 RAG Pipeline Evaluation Test ---")
    
    for query in test_queries:
        print(f"\n[QUERY]: {query}")
        start_time = time.time()
        
        try:
            response = requests.post(API_URL, json={"query": query, "chat_history": []}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"[ANSWER]: {data['answer']}")
                print(f"[METRICS]: Retrieved {len(data['citations'])} chunks.")
                for cit in data['citations']:
                    print(f"   -> Source: {cit['source']}, Page: {cit['page']}")
            else:
                print(f"[ERROR]: API returned status {response.status_code}")
        except Exception as e:
            print(f"[ERROR]: {e}")
            
        print(f"[LATENCY]: {round((time.time() - start_time) * 1000)} ms")

if __name__ == "__main__":
    run_eval_queries()
