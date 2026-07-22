import json

chunks = json.load(open('data/processed/chunks.json', encoding='utf-8'))

c1 = next(c for c in chunks if c['chunk_id'] == 'pump_manual_p1_c1')
c2 = next(c for c in chunks if c['chunk_id'] == 'pump_manual_p1_c2')

w1 = c1['text'].split()
w2 = c2['text'].split()

overlap1 = w1[-90:]
overlap2 = w2[:90]

print('Overlap matches:', overlap1 == overlap2)

if overlap1 == overlap2:
    print('Exact 90-word overlap confirmed')
else:
    print('Overlap mismatch!')