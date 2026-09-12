import os
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_full_rag_pipeline():
    print("=== Testing Full RAG Pipeline End-to-End ===")
    
    # 1. Health check
    res = requests.get(f"{BASE_URL}/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] Health Check passed:", res.json())

    # 2. Guest Login
    res = requests.post(f"{BASE_URL}/api/auth/guest")
    assert res.status_code == 200, f"Guest login failed: {res.text}"
    auth_data = res.json()
    token = auth_data["access_token"]
    user = auth_data["user"]
    print(f"[PASS] Guest Login successful: {user['username']} ({user['id']})")
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Upload Sample Document
    sample_file_path = os.path.join(os.getcwd(), "sample_docs", "deep_learning_system_overview.txt")
    assert os.path.exists(sample_file_path), "Sample file does not exist"
    
    with open(sample_file_path, "rb") as f:
        files = [("files", ("deep_learning_system_overview.txt", f, "text/plain"))]
        res = requests.post(f"{BASE_URL}/api/documents/upload", headers=headers, files=files)
    
    assert res.status_code == 200, f"Document upload failed: {res.text}"
    upload_data = res.json()
    print("[PASS] Document uploaded successfully:", upload_data)
    uploaded_doc_id = upload_data["results"][0]["id"]
    chunks_indexed = upload_data["results"][0]["chunks_indexed"]
    print(f"    Indexed {chunks_indexed} chunks into ChromaDB.")

    # 4. Inspect Document Chunks
    res = requests.get(f"{BASE_URL}/api/documents/{uploaded_doc_id}/chunks", headers=headers)
    assert res.status_code == 200, f"Get chunks failed: {res.text}"
    chunks_data = res.json()
    print(f"[PASS] Retrieved {chunks_data['count']} chunks from ChromaDB for inspection.")

    # 5. Ask Question to RAG Pipeline
    question = "What is the answer accuracy and hallucination rate of Project Titan?"
    print(f"\nAsking Query: '{question}'")
    query_payload = {
        "query": question,
        "document_id": uploaded_doc_id,
        "top_k": 3
    }
    res = requests.post(f"{BASE_URL}/api/chat/query", headers=headers, json=query_payload)
    assert res.status_code == 200, f"Query failed: {res.text}"
    answer_data = res.json()
    print("\n=== AI Answer Received ===")
    print(f"Provider: {answer_data.get('provider')}")
    print(f"Latency: {answer_data.get('latency_ms')}ms")
    print(f"Total Chunks Searched: {answer_data.get('total_chunks_searched')}")
    print(f"Citations ({len(answer_data.get('citations', []))}):")
    for c in answer_data.get("citations", []):
        print(f"  - [Doc: {c['filename']}, Page: {c['page_number']}] Match: {int(c['similarity_score']*100)}%")
    print("\nAnswer Body:")
    print(answer_data.get("answer"))

    # Verify expected keywords in answer or citations
    assert len(answer_data.get("citations", [])) > 0, "Expected at least 1 citation"
    assert "96.4%" in answer_data.get("answer") or "0.8%" in answer_data.get("answer") or "Titan" in answer_data.get("answer"), "Expected factual evidence in answer"
    print("\n[PASS] Factual evidence verification passed!")

    # 6. Verify Chat History
    res = requests.get(f"{BASE_URL}/api/chat/history", headers=headers)
    assert res.status_code == 200, f"History failed: {res.text}"
    history_data = res.json()
    print(f"[PASS] Chat History contains {len(history_data['history'])} turns.")

    print("\n=== ALL E2E VERIFICATION CHECKS PASSED! ===")

if __name__ == "__main__":
    test_full_rag_pipeline()
