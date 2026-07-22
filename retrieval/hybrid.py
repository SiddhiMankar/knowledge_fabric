import re
from retrieval.vector_store import search
from kg.graph_store import G, get_structured_relations

# ---------------------------------------------------------------------------
# Asset ID regex
# ---------------------------------------------------------------------------
ASSET_PATTERN = r'PUMP-\d+|P-\d+|V-\d+|C-\d+|B-\d+'

# Doc-type evidence quotas (prevents any one doc type from dominating context)
DOC_TYPE_QUOTAS = {
    "failure_log": 2,
    "inspection":  2,
    "maintenance": 2,
    "sop":         1,
    "manual":      1,
}


def extract_asset_ids(text):
    """Extracts and deduplicates asset IDs from text, normalized to uppercase."""
    found = re.findall(ASSET_PATTERN, text.upper())
    return list(dict.fromkeys(found))  # preserve order, deduplicate


def graph_lookup(asset_id):
    """
    Returns simple relation dicts (entity + relation) for the given asset.
    Used by rag.py for backwards-compatible graph_context formatting.
    """
    asset_id = asset_id.upper()
    neighbors = []
    if asset_id in G:
        for neighbor in G.neighbors(asset_id):
            relation = G.edges[asset_id, neighbor].get("relation", "CONNECTED_TO")
            neighbors.append({"entity": neighbor, "relation": relation})
    return neighbors


def keyword_search(asset_id, all_chunks):
    """
    Filters all processed chunks to find those that explicitly list
    the given asset_id in their metadata asset_ids.
    """
    results = []
    for chunk in all_chunks:
        metadata = chunk.get("metadata", {})
        raw_assets = metadata.get("asset_ids", [])
        if isinstance(raw_assets, str):
            asset_ids = [a.strip().upper() for a in raw_assets.split(",") if a.strip()]
        else:
            asset_ids = [str(a).upper() for a in raw_assets]

        if asset_id.upper() in asset_ids:
            results.append(chunk)
    return results


def _classify_source(source):
    """Map a source filename to a doc_type quota bucket."""
    s = source.lower()
    if "failure" in s or "fail" in s:
        return "failure_log"
    if "inspection" in s or "inspect" in s:
        return "inspection"
    if "maintenance" in s or "history" in s:
        return "maintenance"
    if "sop" in s or "shutdown" in s or "procedure" in s:
        return "sop"
    return "manual"


def _apply_quotas(chunks):
    """
    Enforce DOC_TYPE_QUOTAS — keep at most N chunks per doc-type bucket.
    Preserves original ordering; excess chunks are dropped.
    """
    counts = {k: 0 for k in DOC_TYPE_QUOTAS}
    kept = []
    for chunk in chunks:
        source = chunk.get("metadata", {}).get("source", "")
        doc_type = _classify_source(source)
        limit = DOC_TYPE_QUOTAS.get(doc_type, 99)
        if counts.get(doc_type, 0) < limit:
            kept.append(chunk)
            counts[doc_type] = counts.get(doc_type, 0) + 1
    return kept


def _asset_consistent(chunk, query_assets):
    """
    Returns True if the chunk is asset-consistent with the query:
      - Generic chunk (no asset_ids tagged) → always keep
      - Tagged chunk → keep only if it shares ≥1 asset with query_assets
    """
    metadata = chunk.get("metadata", {})
    raw_assets = metadata.get("asset_ids", [])
    if isinstance(raw_assets, str):
        chunk_assets = {a.strip().upper() for a in raw_assets.split(",") if a.strip()}
    else:
        chunk_assets = {str(a).upper() for a in raw_assets}

    if not chunk_assets:          # generic chunk — keep
        return True
    return bool(query_assets & chunk_assets)


def merge_results(vector_results, keyword_results, graph_results):
    """
    Merges vector, keyword, and graph results into a single list
    without introducing duplicate document chunks.
    """
    merged = []
    seen_identifiers = set()

    for r in vector_results:
        r_copy = dict(r)
        r_copy["retrieval_type"] = "semantic"
        merged.append(r_copy)
        seen_identifiers.add(r_copy.get("chunk_id") or r_copy.get("text", ""))

    for r in keyword_results:
        identifier = r.get("chunk_id") or r.get("text", "")
        if identifier in seen_identifiers:
            continue
        r_copy = dict(r)
        r_copy["retrieval_type"] = "keyword"
        r_copy.setdefault("score", 0.0)
        merged.append(r_copy)
        seen_identifiers.add(identifier)

    for r in graph_results:
        merged.append({
            "retrieval_type": "graph",
            "text": f"{r['entity']} ({r['relation']})",
            "metadata": {"source": "knowledge_graph"},
            "score": 1.0,
        })

    return merged


def hybrid_retrieve(query, all_chunks, top_k=5):
    """
    Evidence-governed hybrid retrieval coordinator.

    Pipeline:
      1. Extract asset IDs from query
      2. Query routing: asset-aware → KG + keyword first, semantic supplement
                        generic   → semantic only
      3. Asset consistency filtering (drop cross-asset chunks)
      4. Doc-type quota enforcement
      5. Compute retrieval confidence
      6. Return merged results + trace
    """
    asset_ids = extract_asset_ids(query)
    query_assets = set(asset_ids)

    trace = {
        "query_assets": asset_ids,
        "vector_candidates": 0,
        "filtered_out_asset_mismatch": 0,
        "kg_relations_used": 0,
        "evidence_quotas_applied": {},
        "final_evidence": [],
        "retrieval_confidence": 0.0,
    }

    # ------------------------------------------------------------------
    # 1. Knowledge graph structured lookup
    # ------------------------------------------------------------------
    graph_results = []
    structured_kg = []
    for asset_id in asset_ids:
        rels = get_structured_relations(asset_id)
        structured_kg.extend(rels)
        # Also keep legacy simple format for merge_results
        graph_results.extend(graph_lookup(asset_id))

    trace["kg_relations_used"] = len(graph_results)

    # ------------------------------------------------------------------
    # 2. Query routing
    # ------------------------------------------------------------------
    if asset_ids:
        # Asset-aware: keyword + graph authoritative, semantic as supplement
        keyword_results_raw = []
        for asset_id in asset_ids:
            keyword_results_raw.extend(keyword_search(asset_id, all_chunks))

        semantic_top_k = min(3, top_k)
    else:
        # Generic query: full semantic search
        keyword_results_raw = []
        semantic_top_k = top_k

    # ------------------------------------------------------------------
    # 3. Semantic search
    # ------------------------------------------------------------------
    vector_raw = search(query, top_k=semantic_top_k)
    vector_results_raw = []
    if vector_raw and "documents" in vector_raw and vector_raw["documents"]:
        docs      = vector_raw["documents"][0]
        ids       = vector_raw.get("ids", [[]])[0]
        metadatas = vector_raw.get("metadatas", [[]])[0]
        distances = vector_raw.get("distances", [[]])[0]

        for i, doc in enumerate(docs):
            dist = distances[i] if i < len(distances) else 0.0
            similarity = max(0.0, min(1.0, (2.0 - dist) / 2.0))

            # Metadata source boost
            source = (metadatas[i] if i < len(metadatas) else {}).get("source", "").lower()
            if "failure" in source:   similarity += 0.15
            elif "maintenance" in source: similarity += 0.10
            elif "inspection" in source:  similarity += 0.05
            elif "sop" in source:         similarity -= 0.10
            similarity = max(0.0, min(1.0, similarity))

            vector_results_raw.append({
                "chunk_id":  ids[i] if i < len(ids) else f"chunk_{i}",
                "text":      doc,
                "metadata":  metadatas[i] if i < len(metadatas) else {},
                "score":     similarity,
            })

    vector_results_raw.sort(key=lambda x: x["score"], reverse=True)
    trace["vector_candidates"] = len(vector_results_raw)

    # ------------------------------------------------------------------
    # 4. Asset consistency filtering (only for asset-aware queries)
    # ------------------------------------------------------------------
    if query_assets:
        filtered_vectors = [r for r in vector_results_raw if _asset_consistent(r, query_assets)]
        filtered_keywords = [r for r in keyword_results_raw if _asset_consistent(r, query_assets)]
        trace["filtered_out_asset_mismatch"] = (
            len(vector_results_raw) - len(filtered_vectors) +
            len(keyword_results_raw) - len(filtered_keywords)
        )
    else:
        filtered_vectors = vector_results_raw
        filtered_keywords = keyword_results_raw

    # ------------------------------------------------------------------
    # 5. Doc-type quotas
    # ------------------------------------------------------------------
    all_doc_chunks = filtered_vectors + filtered_keywords
    quota_kept = _apply_quotas(all_doc_chunks)

    # Re-split into semantic / keyword after quota enforcement
    seen_quota = set()
    vector_results = []
    keyword_results = []
    for chunk in quota_kept:
        cid = chunk.get("chunk_id") or chunk.get("text", "")
        if chunk in filtered_vectors and cid not in seen_quota:
            vector_results.append(chunk)
            seen_quota.add(cid)
        elif chunk in filtered_keywords and cid not in seen_quota:
            keyword_results.append(chunk)
            seen_quota.add(cid)

    # Count applied quotas for trace
    bucket_counts = {}
    for chunk in quota_kept:
        source = chunk.get("metadata", {}).get("source", "")
        dt = _classify_source(source)
        bucket_counts[dt] = bucket_counts.get(dt, 0) + 1
    trace["evidence_quotas_applied"] = bucket_counts
    trace["final_evidence"] = list({
        chunk.get("metadata", {}).get("source", "unknown")
        for chunk in quota_kept
    })

    # ------------------------------------------------------------------
    # 6. Retrieval confidence
    # ------------------------------------------------------------------
    confidence = 0.0
    if graph_results:
        confidence += 0.5
    if keyword_results:
        confidence += 0.3
    if vector_results and vector_results[0].get("score", 0.0) >= 0.80:
        confidence += 0.2
    confidence = round(confidence, 2)
    trace["retrieval_confidence"] = confidence

    # ------------------------------------------------------------------
    # 7. Merge
    # ------------------------------------------------------------------
    merged = merge_results(vector_results, keyword_results, graph_results)

    return {
        "query":            query,
        "asset_ids":        asset_ids,
        "vector_results":   vector_results,
        "keyword_results":  keyword_results,
        "graph_results":    graph_results,
        "structured_kg":    structured_kg,
        "merged_results":   merged,
        "trace":            trace,
    }
