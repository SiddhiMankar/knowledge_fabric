from retrieval.vector_store import search
import sys

print("--- Running Retrieval E2E Verification ---")
query = 'What causes seal leakage in pump P-101?'
print(f"Query: '{query}'")

try:
    results = search(query, top_k=5)
    documents = results['documents'][0]
    distances = results['distances'][0]
    
    print(f"Number of retrieved documents: {len(documents)}")
    
    # Assert that we get between 3 and 5 documents
    assert 3 <= len(documents) <= 5, f"Expected 3-5 documents, got {len(documents)}"
    
    print("\nRetrieved documents list:")
    for i, doc in enumerate(documents, 1):
        dist = distances[i-1]
        print(f"\n--- Result {i} (Distance: {dist:.4f}) ---")
        print(doc[:300] + "...")
        
    print("\n--- E2E Retrieval Verification Passed Successfully! ---")
    sys.exit(0)
except Exception as e:
    print(f"\nERROR: Retrieval verification failed with exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
