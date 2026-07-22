from retrieval.hybrid import hybrid_retrieve
from processing.chunk_store import load_chunks   # or wherever your chunks are loaded from

chunks = load_chunks('data/processed/chunks.json')

result = hybrid_retrieve(
    'Why did Pump P-101 fail repeatedly?',
    chunks
)

print('Assets:', result['asset_ids'])
print('Graph:', result['graph_results'])
print('Merged count:', len(result['merged_results']))