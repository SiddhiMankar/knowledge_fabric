import json

chunks = json.load(open('data/processed/chunks.json', encoding='utf-8'))

print('='*50)
print('KNOWLEDGE FABRIC – PHASE 2 SANITY CHECK')
print('='*50)

print(f'Total chunks: {len(chunks)}')

ids = [c['chunk_id'] for c in chunks]
print('Unique IDs:', len(ids) == len(set(ids)))

for c in chunks:
    words = len(c['text'].split())
    print(f"{c['chunk_id']}: {words} words | page {c['metadata']['page']} | assets {c['metadata']['asset_ids']}")

print('='*50)
print('Phase 2 verification complete')