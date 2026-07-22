# Phase 5 Progress Report: Hybrid Retrieval

**Completion Date:** July 22, 2026

We have completed Phase 5 — Hybrid Retrieval. The search pipeline coordinates semantic search (vector database), explicit asset-ID keyword filtering, and structured relations lookup from the NetworkX knowledge graph.

---

## 1. Hybrid Retrieval Architecture (`retrieval/hybrid.py`)
Created the unified pipeline [hybrid.py](file:///c:/Projects/knowledge_fabric/retrieval/hybrid.py) implementing:
- **Asset ID Extraction**: Parses queries using the regex `PUMP-\d+|P-\d+|V-\d+|C-\d+|B-\d+` to normalize and identify equipment tags (e.g., `P-101`).
- **Graph Lookup**: Connects with [graph_store.py](file:///c:/Projects/knowledge_fabric/kg/graph_store.py) to retrieve neighbors and relation tags.
- **Keyword Filtering**: Scans all indexed document chunks to find explicit asset tags in their metadata.
- **Metadata-Boosted Ranking**: After vector search, similarity scores are adjusted based on source metadata. We apply a +0.15 boost for failure logs, +0.10 for maintenance logs, +0.05 for inspections, and a -0.10 penalty for SOP documents. Chunks are re-sorted to demote SOP guidelines and prioritize actual failures.
- **Deduplicating Merger**: Combines semantic results, keyword matches, and graph relations into a single evidence list while filtering out duplicate document chunks.

---

## 2. Knowledge Graph Store (`kg/graph_store.py`)
Initialized the knowledge graph store [graph_store.py](file:///c:/Projects/knowledge_fabric/kg/graph_store.py) with relationships for P-101:
- `P-101` ➔ `FAILED_DUE_TO` ➔ `bearing wear`
- `P-101` ➔ `USES_COMPONENT` ➔ `Seal-23`
Additional equipment nodes (P-102, V-101) are included to provide a realistic base layout.

---

## 3. UI Dashboard & RAG Prompt Updates (`app.py` & `retrieval/rag.py`)
- **🕸️ Knowledge Graph Relations**: Renders relationship links dynamically as badges in the Streamlit search panel.
- **🤖 Graph Context in LLM**: Graph relation paths are formatted as `P-101 {relation} {entity}` and passed into the `PROMPT_TEMPLATE` via `{graph_context}`.
- **🗃️ Unified Evidence List**: Displays unified cards for all matching elements, tagged with their respective retrieval type (`[Semantic Match]`, `[Keyword Match]`, and `[Graph Relation]`).

---

## 4. Verification Checkpoint

### A. Programmatic Verification (Metadata Boost & Ranking)
We executed the verification query to verify the boosted document ranking:
```powershell
python -c "from retrieval.hybrid import hybrid_retrieve; import json; chunks=json.load(open('data/processed/chunks.json', encoding='utf-8')); r=hybrid_retrieve('Why did Pump P-101 fail repeatedly?', chunks); print([(x['metadata'].get('source'), x['score']) for x in r['vector_results']])"
```

**Output**:
```text
[
  ('failure_log.txt', 0.9575), 
  ('inspection_report.pdf', 0.7922), 
  ('pump_manual.pdf', 0.7422), 
  ('pump_manual.pdf', 0.7221), 
  ('SOP_shutdown.pdf', 0.7056)
]
```
*Note: `failure_log.txt` is successfully boosted to the top rank, and `SOP_shutdown.pdf` is demoted.*

### B. Programmatic RAG Verification (Prompt Format)
We ran the RAG verification command to confirm the LLM response layout:
```powershell
python -c "from retrieval.vector_store import search; from retrieval.rag import generate_answer; r=search('Why did Pump P-101 fail repeatedly?'); ans=generate_answer('Why did Pump P-101 fail repeatedly?', r); print(ans['answer'])"
```

**Output**:
```text
Root cause:
Pump P-101 failed repeatedly due to scoring on the shaft sleeve and possible cooling water contamination.

Supporting evidence:
- 2026-04-02 07:55 Seal leakage recurred during continuous operation.
- 2026-04-02 10:15 Inspection found scoring on the shaft sleeve and possible cooling water contamination.

Reasoning:
The seal leakage recurred despite previous repairs, indicating an underlying issue. The inspection found scoring on the shaft sleeve, which is a sign of wear, and possible cooling water contamination, which can damage pump components. This evidence suggests that the root cause is related to the pump's internal condition rather than simple mechanical seal failure.

Sources:
- Pump P-101 Shutdown Procedure
- Pump P-101 Restart Procedure
- The Importance of Troubleshooting Your Sulzer vertical pump
- Checkpoints for Initial Start-up of a Vertical Pump
- Vertical Pump Impeller Adjustment
```

### C. Visual UI Verification
The browser subagent verified the Streamlit query layout. The dashboard displays the RAG response, KG relation links, and the unified evidence cards:

![Hybrid Search UI Verification](file:///C:/Users/Siddhi/.gemini/antigravity-ide/brain/92d49da4-9ca2-4957-b4aa-9e7ad8fd4bd6/search_results_success_1784734253775.png)
