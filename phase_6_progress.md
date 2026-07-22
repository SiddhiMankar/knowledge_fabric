# Phase 6 Progress Report: Evidence-Governed Retrieval Policy Redesign

**Completion Date:** July 22, 2026

We have completed Phase 6 — Retrieval Policy Redesign. The platform has been transformed from semantic summarization into an **evidence-governed reasoning engine**, where the Knowledge Graph provides authoritative causal hypotheses, retrieval is strictly constrained to asset-consistent supporting evidence, and confidence gating prevents hallucinated root causes.

**Verification:** All 12/12 automated tests passed.

---

## 1. End-to-End Architecture

```text
User Query
   │
   ▼
[1] Asset Extractor
   - Regex: P-\d+, C-\d+, B-\d+, V-\d+
   - Output: ['P-101']
   │
   ▼
[2] Query Router
   IF asset present:
      keyword search (authoritative)
      graph lookup
      semantic search (top_k=3)
   ELSE:
      semantic search (top_k=5)
   │
   ▼
[3] Asset Consistency Filter
   - Remove chunks tagged with different asset IDs
   - Keep generic chunks (no asset tag)
   │
   ▼
[4] Doc-Type Quota Enforcer
   failure_log ≤ 2
   inspection ≤ 2
   maintenance ≤ 2
   sop ≤ 1
   manual ≤ 1
   │
   ▼
[5] Retrieval Confidence Calculator
   KG hit        +0.5
   Keyword hit   +0.3
   Strong vector +0.2
   │
   ├── confidence < 0.5 → REFUSE TO ANSWER (Hallucination Gate)
   └── confidence ≥ 0.5 → continue
   ▼
[6] Fact Table Builder
   - Extract measured parameters (92°C, 7.8 mm/s, etc.)
   │
   ▼
[7] Root Cause Determiner
   - Read FAILED_DUE_TO from KG
   - Set pre-determined root cause
   │
   ▼
[8] LLM Explanation Layer
   - Explain evidence
   - Do NOT discover root cause from scratch
   │
   ▼
Final Output Payload
- Answer
- Root cause
- Root cause source
- Confidence score
- Unified evidence list
- Retrieval trace
```

---

## 2. Key Accomplishments

### A. Authoritative Knowledge Graph & Priorities (`kg/graph_store.py`)
- Established structured evidence priority constants:
  - `KG_PRIORITY = 100` (Authoritative Causal Evidence)
  - `MEASURED_PRIORITY = 80` (Quantitative Sensor / Log Data)
  - `TREND_PRIORITY = 60`
  - `MAINTENANCE_PRIORITY = 40`
  - `MANUAL_PRIORITY = 20` (Procedural Context Only)
- Expanded equipment graph nodes with `C-201` (`impeller fouling`, `Valve-7`), `B-301` (`belt slippage`, `Filter-12`), `P-102`, and `V-101`.
- Added `get_structured_relations(asset_id)` returning typed relation objects with priority=100 and confidence scores.

### B. Query Routing & Asset Consistency Filtering (`retrieval/hybrid.py`)
- **Query Routing**: Asset-aware queries (`P-101`, `C-201`, etc.) route directly to keyword search and KG lookups, using semantic search only as a top_k=3 supplement. Generic queries use standard top_k=5 vector search.
- **Asset Consistency Filtering**: Automatically discards semantic chunks tagged with a different asset ID than the query, eliminating cross-asset context contamination. Untagged generic chunks are retained.
- **Doc-Type Evidence Quotas**: Enforces strict context limits (`failure_log: 2`, `inspection: 2`, `maintenance: 2`, `sop: 1`, `manual: 1`) to ensure context diversity.
- **Retrieval Trace**: Computes and returns a diagnostic `trace` dict capturing candidate counts, filtered mismatches, applied quotas, final sources, and overall retrieval confidence.

### C. Pre-Determined Root Cause & Fact Table Generator (`retrieval/rag.py`)
- **Retrieval Confidence Gate**: Computes a confidence score (KG +0.5, Keyword +0.3, Top Vector +0.2). If `confidence < 0.5`, the system halts inference and returns an explicit insufficient evidence notice (`root_cause_source: "insufficient_evidence"`).
- **Pre-Determined Root Cause Injection**: Extracts `FAILED_DUE_TO` relations from the KG before prompting the LLM, setting the causal hypothesis directly from graph data (`bearing wear`, confidence 0.95).
- **Fact Table Generator**: Scans documents for measured parameters (e.g. `92°C`, `7.8 mm/s`) and passes a normalized markdown `FACT TABLE` to the LLM for quantitative reasoning.
- **Root Cause Payload**: Returns enriched metadata including `root_cause_source` (`knowledge_graph`, `llm_inference`, or `insufficient_evidence`) and `root_cause_confidence`.

### D. UI Enhancements & Trace Debugger (`app.py`)
- **Root Cause Badges**: Displays badges for root cause source, root cause entity name, confidence level, and retrieval confidence score.
- **Evidence Selection Trace Expander**: Added an expandable dashboard panel (`🔍 Evidence Selection Trace`) displaying query assets, candidate counts, asset mismatch drop counts, applied doc-type quotas, final sources, and confidence scores.

---

## 3. Stage Output Definitions & Verification Rules

| Stage | Input | Expected Output | Verification Rule |
|-------|-------|-----------------|-------------------|
| **Stage 1 — Asset Extractor** | `"Why did Pump P-101 fail repeatedly?"` | `['P-101']` | Must return exact asset tag; no extra words. |
| **Stage 2 — KG Lookup** | `asset_id = "P-101"` | `[{'relation': 'FAILED_DUE_TO', 'target': 'bearing wear', 'priority': 100, 'confidence': 0.95}]` | Priority = 100, Confidence ≥ 0.90, `FAILED_DUE_TO` present. |
| **Stage 3 — Asset Filter** | `[P-101 chunks, C-201 chunks, generic SOP]` | `[P-101 chunks, generic SOP]` | `compressor_failure_log.txt` MUST be removed. |
| **Stage 4 — Quota Enforcement** | `[5 failure logs, 2 SOPs, 3 manuals]` | `[2 failure logs, 1 SOP, 1 manual]` | No doc-type exceeds configured limit. |
| **Stage 5 — Confidence Gate** | `KG hit (+0.5) + Keyword hit (+0.3) + Vector hit (+0.2)` | `confidence = 1.0` (or `0.0` for unindexed asset) | If `< 0.5`, system MUST refuse to answer. |
| **Stage 6 — Fact Table** | Raw chunk snippets with values | `\| P-101 \| bearing temperature \| 92°C \| failure_log.txt \|` | Preserves parameter, unit, and source. |
| **Stage 7 — Root Cause Determiner** | KG relation target | `{'root_cause': 'bearing wear', 'root_cause_source': 'knowledge_graph'}` | Source MUST equal `"knowledge_graph"`. |

---

## 4. Automated 12-Test Verification Suite (`tests/verify_phase6.py`)

We created a comprehensive automated verification suite [tests/verify_phase6.py](file:///c:/Projects/knowledge_fabric/tests/verify_phase6.py) covering all architectural guarantees:

```powershell
venv\Scripts\python tests/verify_phase6.py
```

### Verification Matrix (12/12 Passed)

| Group | Test # | Name | Verification Requirement | Status |
|-------|--------|------|--------------------------|--------|
| **Group A** | **Test 1** | Asset Extraction | Returns exact asset tag `['P-101']` without extra words | ✅ PASS |
| | **Test 2** | KG Authority | `FAILED_DUE_TO` present, `priority == 100`, `confidence >= 0.9` | ✅ PASS |
| | **Test 3** | Asset-Aware Routing | Uses `top_k <= 3` vector supplement and triggers KG lookup | ✅ PASS |
| | **Test 4** | Generic Routing | Uses `top_k == 5` without asset filter for non-asset queries | ✅ PASS |
| | **Test 5** | Asset Consistency Filter | Strips `C-201` chunks during `P-101` query; keeps generic chunks | ✅ PASS |
| | **Test 6** | Quota Enforcement | Enforces limits (`failure ≤ 2`, `inspection ≤ 2`, `manual ≤ 1`, `sop ≤ 1`) | ✅ PASS |
| **Group B** | **Test 7** | Confidence Calculation | Full evidence returns `retrieval_confidence == 1.0` | ✅ PASS |
| | **Test 8** | Hallucination Gate | Unindexed `V-999` returns `confidence == 0.0` & `insufficient_evidence` | ✅ PASS |
| | **Test 9** | Fact Table Extraction | Preserves exact quantitative units (`92°C`, `7.8 mm/s`) | ✅ PASS |
| **Group C** | **Test 10** | KG Determines Root Cause | Root cause set to `bearing wear` with source `knowledge_graph` | ✅ PASS |
| | **Test 11** | Cross-Asset Isolation | `C-201` search contains compressor files and zero `P-101` files | ✅ PASS |
| **Group D** | **Test 12** | Full Regression Suite | 5 end-to-end regression queries (`P-101`, `C-201`, `SOP`, `V-999`, `Patterns`) | ✅ PASS |

---

### Execution Log:
```text
==========================================================
      PHASE 6 REASONING PLATFORM: 12-TEST SUITE           
==========================================================

--- GROUP A: Component-Level Tests ---
[TEST 1/12] Asset Extraction...
 -> TEST 1 PASSED: Asset extraction returned exactly ['P-101']

[TEST 2/12] KG Authority...
 -> TEST 2 PASSED: KG priority 100, confidence 0.95 for target 'bearing wear'

[TEST 3/12] Asset-Aware Query Routing...
 -> TEST 3 PASSED: Asset-aware routing used top_k <= 3 and triggered KG lookup

[TEST 4/12] Generic Query Routing...
 -> TEST 4 PASSED: Generic routing used full top_k = 5 without asset filter

[TEST 5/12] Asset Consistency Filter...
 -> TEST 5 PASSED: Cross-asset C-201 chunk removed; P-101 and generic chunks retained

[TEST 6/12] Doc-Type Quota Enforcement...
 -> TEST 6 PASSED: Quotas strictly enforced (counts: {'failure': 2, 'inspection': 2, 'manual': 1, 'sop': 1})

--- GROUP B: Retrieval Validation Tests ---
[TEST 7/12] Retrieval Confidence Calculation...
 -> TEST 7 PASSED: Full evidence available yields confidence == 1.0

[TEST 8/12] Hallucination Gate (V-999)...
 -> TEST 8 PASSED: Confidence gate halted inference and returned insufficient_evidence payload

[TEST 9/12] Fact Table Parameter & Unit Extraction...
 -> TEST 9 PASSED: Extracted parameters preserve exact units (e.g. ['92 °C', '7.8 mm/s'])

--- GROUP C: Root Cause Governance Tests ---
[TEST 10/12] KG Determines Root Cause...
 -> TEST 10 PASSED: KG authoritative root cause 'bearing wear' determined

[TEST 11/12] Cross-Asset Isolation (C-201 Query)...
 -> TEST 11 PASSED: C-201 evidence isolated cleanly from P-101 files (['compressor_inspection.txt', 'compressor_failure_log.txt'])

--- GROUP D: Full Query Regression Suite (5 Queries) ---
[TEST 12.1/12] Regression Query 1: 'Why did Pump P-101 fail repeatedly?' -> Query 1 PASSED
[TEST 12.2/12] Regression Query 2: 'What failed in C-201?' -> Query 2 PASSED
[TEST 12.3/12] Regression Query 3: 'What is the shutdown procedure?' -> Query 3 PASSED
[TEST 12.4/12] Regression Query 4: 'What failed in V-999?' -> Query 4 PASSED
[TEST 12.5/12] Regression Query 5: 'What are recurring failure patterns for P-101?' -> Query 5 PASSED

==========================================================
   PHASE 6 VERIFICATION COMPLETE: ALL 12/12 TESTS PASSED  
==========================================================
```

