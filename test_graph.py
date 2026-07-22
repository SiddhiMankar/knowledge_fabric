from kg.graph_store import G

print('Nodes:', list(G.nodes())[:10])
print('Edges:')
for u, v, data in G.edges(data=True):
    print(f'{u} --{data["relation"]}--> {v}')