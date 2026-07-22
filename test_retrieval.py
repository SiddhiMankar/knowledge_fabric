import pytest
from retrieval.vector_store import search

@pytest.mark.dependency()
def test_retrieval_e2e():
    """End‑to‑end verification of the retrieval pipeline.
    Ensures that a realistic query returns a sensible number of documents
    and that each result is non‑empty.
    """
    query = "What causes seal leakage in pump P-101?"
    try:
        results = search(query, top_k=5)
        documents = results["documents"][0]
        distances = results["distances"][0]
        # Expect between 3 and 5 documents for this demo corpus
        assert 3 <= len(documents) <= 5, f"Expected 3‑5 documents, got {len(documents)}"
        for i, doc in enumerate(documents, 1):
            dist = distances[i - 1]
            assert doc, f"Document {i} is empty"
            # Optional debugging output captured by pytest
            print(f"--- Result {i} (Distance: {dist:.4f}) ---")
            print(doc[:300] + "...")
    except Exception as e:
        pytest.fail(f"Retrieval verification failed: {e}")
