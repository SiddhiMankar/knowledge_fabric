# Knowledge Fabric

> **Multi-Format Industrial Knowledge Platform with Evidence-Governed RAG**

Knowledge Fabric is an industrial reliability assistant that ingests heterogeneous documents (PDFs, Excel sheets, images, text files), builds a semantic vector index and a structured knowledge graph, and answers equipment-specific questions through an evidence-governed reasoning pipeline — not a simple chatbot.

---

## What It Does

Given a query like **"Why did Pump P-101 fail repeatedly?"**, the system:

1. **Detects the asset ID** (`P-101`) using regex extraction
2. **Routes the query** to authoritative keyword evidence and KG relations first
3. **Filters semantic results** to only asset-consistent chunks
4. **Applies doc-type quotas** (max 2 failure logs, 2 inspections, 1 SOP, 1 manual)
5. **Extracts a pre-determined root cause** from the Knowledge Graph (`bearing wear`)
6. **Gates on retrieval confidence** — refuses to answer if evidence is insufficient
7. **Passes a structured fact table** to the LLM for quantitative reasoning
8. Returns a traceable answer with **root cause source**, **confidence score**, and a **retrieval trace**

---

## Tech Stack

| Layer | Technology |
|---|---|
| **UI** | [Streamlit](https://streamlit.io/) |
| **LLM** | [Groq API](https://groq.com/) — `llama-3.1-8b-instant` |
| **Vector Store** | [ChromaDB](https://www.trychroma.com/) (cosine metric space) |
| **Embeddings** | [Sentence-Transformers](https://www.sbert.net/) — `all-MiniLM-L6-v2` |
| **Knowledge Graph** | [NetworkX](https://networkx.org/) |
| **PDF Parsing** | [PyMuPDF](https://pymupdf.readthedocs.io/) (`fitz`) |
| **Image OCR** | [Tesseract](https://github.com/tesseract-ocr/tesseract) via `pytesseract` |
| **Excel Parsing** | [openpyxl](https://openpyxl.readthedocs.io/) |
| **DOCX Parsing** | [python-docx](https://python-docx.readthedocs.io/) |
| **ML Framework** | [PyTorch](https://pytorch.org/) + [Torchvision](https://pytorch.org/vision/) |
| **Environment** | [python-dotenv](https://pypi.org/project/python-dotenv/) |
| **Language** | Python 3.12+ |

---

## Project Structure

```
knowledge_fabric/
├── app.py                        # Streamlit UI — ingestion + search tabs
│
├── ingestion/                    # Document loaders
│   ├── loader.py                 # Router: dispatches to correct loader by type
│   ├── pdf_loader.py             # PyMuPDF page-wise PDF extraction
│   ├── excel_loader.py           # openpyxl multi-sheet Excel loader
│   ├── image_loader.py           # PIL + Tesseract OCR loader
│   ├── text_loader.py            # Plain text / DOCX loader
│   └── ocr_utils.py              # Tesseract preprocessing helpers
│
├── processing/
│   ├── chunker.py                # Word-based chunker (600w, 90w overlap) + asset tag extraction
│   └── chunk_store.py            # load_chunks() helper
│
├── retrieval/
│   ├── vector_store.py           # ChromaDB client — index_chunks(), search()
│   ├── hybrid.py                 # Hybrid retrieval coordinator (routing, filtering, quotas, trace)
│   └── rag.py                   # RAG answer engine (Groq, pre-determined root cause, fact table)
│
├── kg/
│   └── graph_store.py            # NetworkX KG — assets, failure modes, components, relations
│
├── demo_docs/                    # Sample industrial documents for demo
│   ├── pump_manual.pdf
│   ├── inspection_report.pdf
│   ├── SOP_shutdown.pdf
│   ├── maintenance_history.xlsx
│   └── failure_log.txt
│
├── data/
│   ├── raw/                      # Uploaded raw files (gitignored)
│   └── processed/
│       └── chunks.json           # Serialized chunk store
│
├── vector_store/                 # ChromaDB persistent storage (gitignored)
│
├── .env                          # API keys (gitignored)
├── requirements.txt
└── phase_*_progress.md           # Phase-by-phase development logs
```

---

## Architecture

```
User Query
   ↓
Asset Extractor      (regex: P-\d+, C-\d+, B-\d+, V-\d+)
   ↓
Query Router
   ├── Keyword Search    → authoritative asset evidence
   ├── KG Lookup         → causal hypothesis (FAILED_DUE_TO)
   └── Semantic Search   → supporting context only (top_k=3)
           ↓
Asset Consistency Filter  (drop cross-asset chunks)
           ↓
Doc-Type Quota Enforcer   (failure×2, inspection×2, sop×1, manual×1)
           ↓
Retrieval Confidence Gate (< 0.5 → refuse to answer)
           ↓
Fact Table Builder        (structured measured data)
           ↓
Root Cause Determiner     (KG FAILED_DUE_TO → pre-determined cause)
           ↓
LLM Explanation Layer     (Groq llama-3.1-8b-instant)
           ↓
Answer + Root Cause Source + Evidence Trace + Confidence Score
```

---

## Retrieval Pipeline

### Evidence Priority Levels

```python
KG_PRIORITY        = 100   # Knowledge graph relations (authoritative)
MEASURED_PRIORITY  = 80    # Sensor readings, temperatures, vibration
TREND_PRIORITY     = 60    # Historical trends
MAINTENANCE_PRIORITY = 40  # Maintenance records
MANUAL_PRIORITY    = 20    # Manuals, SOPs (procedural only)
```

### Doc-Type Quotas

```python
DOC_TYPE_QUOTAS = {
    "failure_log":  2,
    "inspection":   2,
    "maintenance":  2,
    "sop":          1,
    "manual":       1,
}
```

### Retrieval Confidence

```python
confidence = 0.0
if graph_relations:                           confidence += 0.5
if keyword_results:                           confidence += 0.3
if semantic_results[0]["score"] >= 0.80:      confidence += 0.2
# If confidence < 0.5 → return insufficient evidence message
```

---

## Knowledge Graph

Built with **NetworkX**. Current relations:

| Asset | Relation | Target |
|-------|----------|--------|
| P-101 | FAILED_DUE_TO | bearing wear |
| P-101 | USES_COMPONENT | Seal-23 |
| P-102 | FAILED_DUE_TO | coupling wear |
| V-101 | FAILED_DUE_TO | inlet valve leakage |

KG relations carry `priority=100` and are injected as the **authoritative pre-determined root cause** before the LLM is prompted.

---

## Getting Started

### Prerequisites

- Python 3.12+
- Tesseract OCR installed and on PATH
- A [Groq API key](https://console.groq.com/)

### Setup

```powershell
# Clone the repo
git clone https://github.com/SiddhiMankar/knowledge_fabric.git
cd knowledge_fabric

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Create a .env file with:
# GROQ_API_KEY=your_key_here
```

### Run

```powershell
streamlit run app.py
```

Navigate to `http://localhost:8501`.

### Ingest Demo Documents

1. Go to **📂 Document Ingestion & Chunking** tab
2. Use the **Developer Test Panel** in the sidebar to load files from `demo_docs/`
3. Click **Ingest File** for each document
4. Switch to **🔍 Semantic Search Engine** tab and query

---

## Development Phases

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Project scaffold, ingestion loaders (PDF, Excel, image, text) | ✅ Complete |
| **Phase 2** | Chunking pipeline, asset ID extraction, metadata tagging | ✅ Complete |
| **Phase 3** | ChromaDB vector store, sentence-transformer embeddings, semantic search | ✅ Complete |
| **Phase 4** | Groq RAG answer engine, dotenv config, prompt template | ✅ Complete |
| **Phase 5** | Hybrid retrieval (KG + keyword + semantic), metadata boosts, unified evidence UI | ✅ Complete |
| **Phase 6** | Evidence-governed reasoning: confidence gate, asset filtering, quotas, fact table, KG authority | 🔄 In Progress |

---

## Key Design Decisions

- **KG is authoritative, not advisory** — `FAILED_DUE_TO` relations produce a pre-determined root cause that the LLM must explain, not discover.
- **Asset consistency filtering** — Chunks mentioning a different asset than the query are dropped even if their embedding similarity is high.
- **Confidence gate** — If the combined evidence score is below 0.5, the system explicitly refuses to guess rather than hallucinating a root cause.
- **Doc-type quotas** — Prevent five nearly-identical failure log chunks from dominating the LLM context; guarantees evidence diversity.
- **Retrieval trace** — Every query returns a trace object showing exactly which chunks were kept, filtered, and why — making the system debuggable and auditable.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Your Groq API key for LLM inference |

---

## License

MIT