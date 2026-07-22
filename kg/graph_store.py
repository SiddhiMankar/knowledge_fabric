import networkx as nx

# Evidence priority levels
KG_PRIORITY = 100
MEASURED_PRIORITY = 80
TREND_PRIORITY = 60
MAINTENANCE_PRIORITY = 40
MANUAL_PRIORITY = 20

# Initialize the knowledge graph
G = nx.Graph()

# ---------------------------------------------------------------------------
# P-101 — Centrifugal Pump
# ---------------------------------------------------------------------------
G.add_node("P-101", type="asset")
G.add_node("bearing wear", type="failure_mode")
G.add_node("Seal-23", type="component")

G.add_edge("P-101", "bearing wear", relation="FAILED_DUE_TO", confidence=0.95)
G.add_edge("P-101", "Seal-23", relation="USES_COMPONENT", confidence=0.90)

# ---------------------------------------------------------------------------
# P-102 — Backup Pump
# ---------------------------------------------------------------------------
G.add_node("P-102", type="asset")
G.add_node("coupling wear", type="failure_mode")

G.add_edge("P-102", "coupling wear", relation="FAILED_DUE_TO", confidence=0.85)

# ---------------------------------------------------------------------------
# C-201 — Centrifugal Compressor
# ---------------------------------------------------------------------------
G.add_node("C-201", type="asset")
G.add_node("impeller fouling", type="failure_mode")
G.add_node("Valve-7", type="component")

G.add_edge("C-201", "impeller fouling", relation="FAILED_DUE_TO", confidence=0.90)
G.add_edge("C-201", "Valve-7", relation="USES_COMPONENT", confidence=0.85)

# ---------------------------------------------------------------------------
# B-301 — Industrial Blower
# ---------------------------------------------------------------------------
G.add_node("B-301", type="asset")
G.add_node("belt slippage", type="failure_mode")
G.add_node("Filter-12", type="component")

G.add_edge("B-301", "belt slippage", relation="FAILED_DUE_TO", confidence=0.88)
G.add_edge("B-301", "Filter-12", relation="USES_COMPONENT", confidence=0.80)

# ---------------------------------------------------------------------------
# V-101 — Control Valve
# ---------------------------------------------------------------------------
G.add_node("V-101", type="asset")
G.add_node("inlet valve leakage", type="failure_mode")

G.add_edge("V-101", "inlet valve leakage", relation="FAILED_DUE_TO", confidence=0.80)


def get_structured_relations(asset_id):
    """
    Returns structured evidence objects for a given asset from the knowledge graph.
    Each object carries an evidence priority, confidence, and relation type.
    KG relations have priority=100 (highest authority in the evidence hierarchy).
    """
    asset_id = asset_id.upper()
    relations = []
    if asset_id not in G:
        return relations

    for neighbor in G.neighbors(asset_id):
        edge_data = G.edges[asset_id, neighbor]
        relation = edge_data.get("relation", "CONNECTED_TO")
        confidence = edge_data.get("confidence", 0.80)

        relations.append({
            "type": "kg_relation",
            "asset": asset_id,
            "relation": relation,
            "target": neighbor,
            "confidence": confidence,
            "priority": KG_PRIORITY,
        })

    # Sort: FAILED_DUE_TO first (causal), then others
    relations.sort(key=lambda r: (r["relation"] != "FAILED_DUE_TO", -r["confidence"]))
    return relations
