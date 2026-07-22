import os
import sys

# Ensure project root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from kg.graph_store import get_structured_relations
from retrieval.hybrid import (
    extract_asset_ids,
    hybrid_retrieve,
    _asset_consistent,
    _apply_quotas
)
from retrieval.rag import generate_answer, _extract_facts


def run_12_test_suite():
    print("==========================================================")
    print("      PHASE 6 REASONING PLATFORM: 12-TEST SUITE           ")
    print("==========================================================")

    chunks_file = 'data/processed/chunks.json'
    assert os.path.exists(chunks_file), f"Error: {chunks_file} missing!"

    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    test_pass_count = 0

    # -------------------------------------------------------------------
    # GROUP A — COMPONENT-LEVEL TESTS
    # -------------------------------------------------------------------
    print("\n--- GROUP A: Component-Level Tests ---")

    # TEST 1 — Asset Extraction
    print("[TEST 1/12] Asset Extraction...")
    extracted = extract_asset_ids("Why did Pump P-101 fail repeatedly?")
    assert extracted == ["P-101"], f"Fail: expected ['P-101'], got {extracted}"
    print(" -> TEST 1 PASSED: Asset extraction returned exactly ['P-101']")
    test_pass_count += 1

    # TEST 2 — KG Authority
    print("\n[TEST 2/12] KG Authority...")
    relations = get_structured_relations("P-101")
    failed_due_to = [r for r in relations if r.get("relation") == "FAILED_DUE_TO"]
    assert failed_due_to, "Fail: No FAILED_DUE_TO relation found for P-101"
    top_rel = failed_due_to[0]
    assert top_rel["target"] == "bearing wear", f"Fail: expected 'bearing wear', got '{top_rel['target']}'"
    assert top_rel["priority"] == 100, f"Fail: priority != 100, got {top_rel['priority']}"
    assert top_rel["confidence"] >= 0.9, f"Fail: confidence < 0.9, got {top_rel['confidence']}"
    print(f" -> TEST 2 PASSED: KG priority 100, confidence {top_rel['confidence']} for target '{top_rel['target']}'")
    test_pass_count += 1

    # TEST 3 — Query Routing (Asset-Aware)
    print("\n[TEST 3/12] Asset-Aware Query Routing...")
    r_asset = hybrid_retrieve("Why did P-101 fail?", chunks)
    t_asset = r_asset['trace']
    assert t_asset['query_assets'] == ["P-101"], f"Fail: expected assets ['P-101'], got {t_asset['query_assets']}"
    assert t_asset['vector_candidates'] <= 3, f"Fail: expected vector top_k <= 3, got {t_asset['vector_candidates']}"
    assert t_asset['kg_relations_used'] >= 1, "Fail: KG lookup not triggered"
    print(" -> TEST 3 PASSED: Asset-aware routing used top_k <= 3 and triggered KG lookup")
    test_pass_count += 1

    # TEST 4 — Generic Query Routing
    print("\n[TEST 4/12] Generic Query Routing...")
    r_gen = hybrid_retrieve("What is the shutdown procedure?", chunks)
    t_gen = r_gen['trace']
    assert t_gen['query_assets'] == [], f"Fail: expected empty query assets, got {t_gen['query_assets']}"
    assert t_gen['vector_candidates'] == 5, f"Fail: expected vector top_k == 5, got {t_gen['vector_candidates']}"
    print(" -> TEST 4 PASSED: Generic routing used full top_k = 5 without asset filter")
    test_pass_count += 1

    # TEST 5 — Asset Consistency Filter
    print("\n[TEST 5/12] Asset Consistency Filter...")
    p101_chunk = {"text": "P-101 log", "metadata": {"asset_ids": ["P-101"]}}
    c201_chunk = {"text": "C-201 log", "metadata": {"asset_ids": ["C-201"]}}
    generic_chunk = {"text": "Generic SOP", "metadata": {"asset_ids": []}}
    mock_chunks = [p101_chunk, c201_chunk, generic_chunk]

    query_assets = {"P-101"}
    filtered = [c for c in mock_chunks if _asset_consistent(c, query_assets)]
    filtered_texts = [c["text"] for c in filtered]

    assert "P-101 log" in filtered_texts, "Fail: P-101 chunk was dropped"
    assert "Generic SOP" in filtered_texts, "Fail: Generic untagged chunk was dropped"
    assert "C-201 log" not in filtered_texts, "Fail: C-201 chunk survived asset filter!"
    print(" -> TEST 5 PASSED: Cross-asset C-201 chunk removed; P-101 and generic chunks retained")
    test_pass_count += 1

    # TEST 6 — Quota Enforcement
    print("\n[TEST 6/12] Doc-Type Quota Enforcement...")
    mock_quota_input = [
        {"metadata": {"source": f"failure_{i}.txt"}} for i in range(5)
    ] + [
        {"metadata": {"source": f"inspection_{i}.pdf"}} for i in range(3)
    ] + [
        {"metadata": {"source": f"manual_{i}.pdf"}} for i in range(4)
    ] + [
        {"metadata": {"source": f"sop_{i}.pdf"}} for i in range(2)
    ]

    quota_output = _apply_quotas(mock_quota_input)
    counts = {}
    for c in quota_output:
        src = c["metadata"]["source"]
        prefix = src.split("_")[0]
        counts[prefix] = counts.get(prefix, 0) + 1

    assert counts.get("failure", 0) <= 2, f"Fail: failure quota exceeded: {counts.get('failure')}"
    assert counts.get("inspection", 0) <= 2, f"Fail: inspection quota exceeded: {counts.get('inspection')}"
    assert counts.get("manual", 0) <= 1, f"Fail: manual quota exceeded: {counts.get('manual')}"
    assert counts.get("sop", 0) <= 1, f"Fail: sop quota exceeded: {counts.get('sop')}"
    print(f" -> TEST 6 PASSED: Quotas strictly enforced (counts: {counts})")
    test_pass_count += 1

    # -------------------------------------------------------------------
    # GROUP B — RETRIEVAL VALIDATION
    # -------------------------------------------------------------------
    print("\n--- GROUP B: Retrieval Validation Tests ---")

    # TEST 7 — Retrieval Confidence Calculation
    print("[TEST 7/12] Retrieval Confidence Calculation...")
    r_p101 = hybrid_retrieve("Why did Pump P-101 fail repeatedly?", chunks)
    conf_p101 = r_p101['trace']['retrieval_confidence']
    assert conf_p101 == 1.0, f"Fail: expected confidence == 1.0, got {conf_p101}"
    print(" -> TEST 7 PASSED: Full evidence available yields confidence == 1.0")
    test_pass_count += 1

    # TEST 8 — Hallucination Gate
    print("\n[TEST 8/12] Hallucination Gate (V-999)...")
    r_v999 = hybrid_retrieve("What failed in V-999?", chunks)
    t_v999 = r_v999['trace']
    assert t_v999['retrieval_confidence'] == 0.0, f"Fail: expected 0.0 confidence, got {t_v999['retrieval_confidence']}"

    boosted_v999 = {
        'documents': [[chunk['text'] for chunk in r_v999['vector_results']]],
        'metadatas': [[chunk['metadata'] for chunk in r_v999['vector_results']]]
    }
    ans_v999 = generate_answer("What failed in V-999?", boosted_v999, confidence=t_v999['retrieval_confidence'])
    assert ans_v999['root_cause_source'] == "insufficient_evidence", f"Fail: expected 'insufficient_evidence', got '{ans_v999['root_cause_source']}'"
    assert ans_v999['root_cause'] is None, f"Fail: expected None root cause, got '{ans_v999['root_cause']}'"
    print(" -> TEST 8 PASSED: Confidence gate halted inference and returned insufficient_evidence payload")
    test_pass_count += 1

    # TEST 9 — Fact Table Extraction
    print("\n[TEST 9/12] Fact Table Parameter & Unit Extraction...")
    p101_docs = [c['text'] for c in chunks if 'P-101' in str(c.get('metadata', {}).get('asset_ids', ''))]
    p101_metas = [c['metadata'] for c in chunks if 'P-101' in str(c.get('metadata', {}).get('asset_ids', ''))]

    facts = _extract_facts(p101_docs, p101_metas, query_assets={"P-101"})
    fact_values = [f["value"] for f in facts]

    temp_fact = any("92" in v and "°C" in v for v in fact_values)
    vib_fact = any("7.8" in v and "mm/s" in v for v in fact_values)

    assert temp_fact, f"Fail: 92°C with unit missing from facts: {fact_values}"
    assert vib_fact, f"Fail: 7.8 mm/s with unit missing from facts: {fact_values}"
    print(f" -> TEST 9 PASSED: Extracted parameters preserve exact units (e.g. {fact_values})")
    test_pass_count += 1

    # -------------------------------------------------------------------
    # GROUP C — ROOT CAUSE GOVERNANCE
    # -------------------------------------------------------------------
    print("\n--- GROUP C: Root Cause Governance Tests ---")

    # TEST 10 — KG Determines Root Cause
    print("[TEST 10/12] KG Determines Root Cause...")
    boosted_p101 = {
        'documents': [[chunk['text'] for chunk in r_p101['vector_results']]],
        'metadatas': [[chunk['metadata'] for chunk in r_p101['vector_results']]]
    }
    ans_p101 = generate_answer("Why did Pump P-101 fail repeatedly?", boosted_p101, confidence=conf_p101)
    assert ans_p101['root_cause'] == "bearing wear", f"Fail: expected 'bearing wear', got '{ans_p101['root_cause']}'"
    assert ans_p101['root_cause_source'] == "knowledge_graph", f"Fail: expected 'knowledge_graph', got '{ans_p101['root_cause_source']}'"
    print(" -> TEST 10 PASSED: KG authoritative root cause 'bearing wear' determined")
    test_pass_count += 1

    # TEST 11 — Cross-Asset Isolation
    print("\n[TEST 11/12] Cross-Asset Isolation (C-201 Query)...")
    r_c201 = hybrid_retrieve("What failed in C-201?", chunks)
    c201_sources = [s.lower() for s in r_c201['trace']['final_evidence']]

    assert any('compressor' in s for s in c201_sources), f"Fail: compressor docs missing in C-201 search: {c201_sources}"
    assert not any('failure_log.txt' == s for s in c201_sources), f"Fail: P-101 failure log leaked into C-201 evidence: {c201_sources}"
    print(f" -> TEST 11 PASSED: C-201 evidence isolated cleanly from P-101 files ({c201_sources})")
    test_pass_count += 1

    # -------------------------------------------------------------------
    # GROUP D — END-TO-END SYSTEM REGRESSION SUITE (5 QUERIES)
    # -------------------------------------------------------------------
    print("\n--- GROUP D: Full Query Regression Suite (5 Queries) ---")

    # Query 1
    print("\n[TEST 12.1/12] Regression Query 1: 'Why did Pump P-101 fail repeatedly?'")
    r1 = hybrid_retrieve("Why did Pump P-101 fail repeatedly?", chunks)
    b1 = {'documents': [[c['text'] for c in r1['vector_results']]], 'metadatas': [[c['metadata'] for c in r1['vector_results']]]}
    a1 = generate_answer("Why did Pump P-101 fail repeatedly?", b1, confidence=r1['trace']['retrieval_confidence'])
    assert a1['root_cause'] == "bearing wear"
    assert a1['root_cause_source'] == "knowledge_graph"
    assert a1['root_cause_confidence'] >= 0.9
    print(" -> Query 1 PASSED")

    # Query 2
    print("\n[TEST 12.2/12] Regression Query 2: 'What failed in C-201?'")
    r2 = hybrid_retrieve("What failed in C-201?", chunks)
    b2 = {'documents': [[c['text'] for c in r2['vector_results']]], 'metadatas': [[c['metadata'] for c in r2['vector_results']]]}
    a2 = generate_answer("What failed in C-201?", b2, confidence=r2['trace']['retrieval_confidence'])
    assert a2['root_cause'] == "impeller fouling"
    assert a2['root_cause_source'] == "knowledge_graph"
    print(" -> Query 2 PASSED")

    # Query 3
    print("\n[TEST 12.3/12] Regression Query 3: 'What is the shutdown procedure?'")
    r3 = hybrid_retrieve("What is the shutdown procedure?", chunks)
    assert any(k in s.lower() for s in r3['trace']['final_evidence'] for k in ['sop', 'shutdown', 'procedure'])
    print(" -> Query 3 PASSED")

    # Query 4
    print("\n[TEST 12.4/12] Regression Query 4: 'What failed in V-999?'")
    r4 = hybrid_retrieve("What failed in V-999?", chunks)
    b4 = {'documents': [[c['text'] for c in r4['vector_results']]], 'metadatas': [[c['metadata'] for c in r4['vector_results']]]}
    a4 = generate_answer("What failed in V-999?", b4, confidence=r4['trace']['retrieval_confidence'])
    assert a4['root_cause_source'] == "insufficient_evidence"
    assert "insufficient evidence" in a4['answer'].lower()
    print(" -> Query 4 PASSED")

    # Query 5
    print("\n[TEST 12.5/12] Regression Query 5: 'What are recurring failure patterns for P-101?'")
    r5 = hybrid_retrieve("What are recurring failure patterns for P-101?", chunks)
    b5 = {'documents': [[c['text'] for c in r5['vector_results']]], 'metadatas': [[c['metadata'] for c in r5['vector_results']]]}
    a5 = generate_answer("What are recurring failure patterns for P-101?", b5, confidence=r5['trace']['retrieval_confidence'])
    ans_text = a5['answer'].lower()
    assert "bearing wear" in ans_text or "seal leakage" in ans_text or "92" in ans_text or "7.8" in ans_text
    print(" -> Query 5 PASSED")

    test_pass_count += 1  # Full regression suite complete

    print("\n==========================================================")
    print(f"   PHASE 6 VERIFICATION COMPLETE: ALL {test_pass_count}/12 TESTS PASSED  ")
    print("==========================================================")

if __name__ == '__main__':
    run_12_test_suite()
