# pyrefly: ignore [missing-import]
import chromadb
# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer

print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Creating ChromaDB client...")
client = chromadb.PersistentClient(path="vector_store")

collection = client.get_or_create_collection("test_collection")

embedding = model.encode("Pump P-101 seal leakage").tolist()

collection.add(
    ids=["1"],
    documents=["Pump P-101 seal leakage"],
    embeddings=[embedding]
)

results = collection.query(
    query_embeddings=[embedding],
    n_results=1
)

print("Query result:")
print(results["documents"][0][0])
print("Setup successful!")