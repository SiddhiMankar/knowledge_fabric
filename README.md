# Knowledge Fabric

> **Multi-Format Industrial Knowledge Platform with Evidence-Governed RAG**

Knowledge Fabric is an industrial reliability intelligence platform built to ingest heterogeneous technical documents (PDFs, multi-sheet Excel workbooks, industrial scan images, Word documents, raw failure logs), build a hybrid semantic vector index and structured Knowledge Graph (KG), and execute evidence-governed reasoning for complex plant operations — eliminating LLM hallucinations through deterministic governance.

---

## 🌟 Key Capabilities & Evaluation Highlights

- 🎯 **Deterministic Root Cause Governance:** Uses NetworkX Knowledge Graph `FAILED_DUE_TO` causal relations with top-tier priority (`priority=100`) as authoritative evidence that the LLM must explain rather than discover.
- 🛡️ **Zero-Hallucination Confidence Gate:** Computes a composite retrieval confidence score ($0.0 \to 1.0$). If evidence score is below $0.5$, inference halts immediately and returns an explicit `insufficient_evidence` notice.
- 🔒 **Asset-Consistent Routing & Filtering:** Automatically extracts asset tags (e.g. `P-101`, `C-201`, `V-999`) from queries via regular expressions. Filters out cross-asset chunks regardless of high vector similarity.
- 📊 **Doc-Type Quotas & Diversity:** Enforces strict quotas per document class (max 2 failure logs, 2 inspection reports, 2 maintenance records, 1 SOP, 1 manual) to prevent any single file from flooding LLM context.
- 🧬 **Quantitative Fact Table:** Automatically compiles sensor readings, temperatures, vibration RMS values, and alignment tolerances into a structured fact table for numerical reasoning.
- 🔍 **Full Execution Auditability:** Renders a real-time **Evidence Selection Trace** for every query, detailing query assets, vector candidates, filtered chunks, KG relations, doc-type quotas, and retrieval confidence.
- 🎨 **Industrial-Grade Streamlit UI:** Refactored dark refinery operation console styled with custom typography (*Outfit* & *Plus Jakarta Sans*), glassmorphism cards, and strict HTML sanitization (`clean_llm_text` + `html.escape`).

---

## 🛠️ Tech Stack

| Layer | Technology | Function |
|---|---|---|
| **UI Framework** | [Streamlit](https://streamlit.io/) | Dark refinery operations console |
| **LLM Inference** | [Groq API](https://groq.com/) | `llama-3.1-8b-instant` |
| **Vector Database** | [ChromaDB](https://www.trychroma.com/) | Persistent vector store with cosine metric space |
| **Embeddings** | [Sentence-Transformers](https://www.sbert.net/) | `all-MiniLM-L6-v2` (384-dimensional dense vectors) |
| **Knowledge Graph** | [NetworkX](https://networkx.org/) | Causal graph & relation store (`G.add_edge`) |
| **PDF Parsing** | [PyMuPDF](https://pymupdf.readthedocs.io/) (`fitz`) | Fast page-wise PDF text extraction |
| **Image OCR** | [pytesseract](https://pypi.org/project/pytesseract/) | Tesseract OCR for technical scans/diagrams |
| **Excel Parsing** | [openpyxl](https://openpyxl.readthedocs.io/) | Multi-sheet table extraction |
| **DOCX Parsing** | [python-docx](https://python-docx.readthedocs.io/) | Word document text & table reader |
| **ML Runtime** | [PyTorch](https://pytorch.org/) | Embedding tensor computations |
| **Environment** | [python-dotenv](https://pypi.org/project/python-dotenv/) | Environment variable management |

---

## 🏗️ Architecture & Pipeline Flow

```
                              User Query
                                  │
                       Asset ID Extractor (regex)
                        (e.g., P-101, C-201, V-999)
                                  │
                          Query Router
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
   KG Lookup             Keyword Search            Semantic Search
(Causal Relations)    (Asset-Tagged Chunks)      (ChromaDB Dense Vectors)
  [Priority 100]           [Priority 80]              [Priority 40-60]
        └─────────────────────────┬─────────────────────────┘
                                  │
                    Asset Consistency Filter
                (Drop cross-asset mismatches)
                                  │
                    Doc-Type Quota Enforcer
              (Max 2 Failure, 2 Inspect, 1 SOP)
                                  │
                   Retrieval Confidence Evaluator
                     (Score < 0.5 Threshold)
                     ┌────────────┴────────────┐
             Score < 0.5               Score ≥ 0.5
                 │                         │
                 ▼                         ▼
      [Refusal Response]          Fact Table Compiler
  "Insufficient Evidence"                  │
                                  Root Cause Determiner
                               (KG Authoritative Cause)
                                           │
                                 LLM Explanation Layer
                                (Groq Llama-3.1-8B)
                                           │
                                💡 Verified Answer Card
                              + Evidence Selection Trace
```

---

## 📁 Project Structure

```
knowledge_fabric/
├── app.py                        # Streamlit Industrial UI (Ingestion & Search tabs)
│
├── ingestion/                    # Multi-format document loader pipeline
│   ├── loader.py                 # Central format router
│   ├── pdf_loader.py             # PyMuPDF extractor
│   ├── excel_loader.py           # openpyxl multi-sheet loader
│   ├── image_loader.py           # PIL + Tesseract OCR engine
│   ├── text_loader.py            # Text & DOCX loader
│   └── ocr_utils.py              # Image preprocessing (grayscale/thresholding)
│
├── processing/                   # Text processing & chunking
│   ├── chunker.py                # Word-based chunker (600w, 90w overlap) + Asset Tagging
│   └── chunk_store.py            # Local JSON chunk store helpers
│
├── retrieval/                    # Reasoning & Retrieval Engine
│   ├── vector_store.py           # ChromaDB client & semantic indexing
│   ├── hybrid.py                 # Hybrid coordinator (Routing, Quotas, Asset Filter, Trace)
│   └── rag.py                    # RAG Answer Engine (Fact table, KG cause, Confidence gate)
│
├── kg/                           # Knowledge Graph
│   └── graph_store.py            # NetworkX graph builder & relation extractor
│
├── tests/                        # Automated Evaluation Suite
│   └── verify_phase6.py          # 12-Test comprehensive reasoning test suite
│
├── demo_docs/                    # Sample industrial test documents
│   ├── pump_manual.pdf
│   ├── inspection_report.pdf
│   ├── SOP_shutdown.pdf
│   ├── maintenance_history.xlsx
│   └── failure_log.txt
│
├── requirements.txt              # Project dependencies
└── README.md                     # System documentation
```

---

## 🚦 Getting Started

### Prerequisites

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed and added to system `PATH`
- A [Groq API Key](https://console.groq.com/)

### 1. Installation

```powershell
# Clone repository
git clone https://github.com/SiddhiMankar/knowledge_fabric.git
cd knowledge_fabric

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## 🧪 Automated Evaluation & Verification

The repository includes a comprehensive 12-test suite that validates component logic, retrieval routing, hallucination gating, fact table extraction, cross-asset isolation, and 5 full query regressions.

Run the test suite via command line:

```powershell
python tests/verify_phase6.py
```

### Test Suite Output Summary:

```
==========================================================
      PHASE 6 REASONING PLATFORM: 12-TEST SUITE           
==========================================================
[TEST 1/12] Asset Extraction               -> PASSED
[TEST 2/12] KG Authority                   -> PASSED
[TEST 3/12] Asset-Aware Query Routing      -> PASSED
[TEST 4/12] Generic Query Routing          -> PASSED
[TEST 5/12] Asset Consistency Filter       -> PASSED
[TEST 6/12] Doc-Type Quota Enforcement     -> PASSED
[TEST 7/12] Retrieval Confidence Calc      -> PASSED
[TEST 8/12] Hallucination Gate (V-999)     -> PASSED
[TEST 9/12] Fact Table Parameter Extract  -> PASSED
[TEST 10/12] KG Determines Root Cause      -> PASSED
[TEST 11/12] Cross-Asset Isolation         -> PASSED
[TEST 12/12] 5-Query Regression Suite      -> PASSED
==========================================================
   PHASE 6 VERIFICATION COMPLETE: ALL 12/12 TESTS PASSED  
==========================================================
```

---

## 💻 Running the Web Application

Launch the Streamlit web console:

```powershell
streamlit run app.py
```

Navigate to `http://localhost:8501`.

### Suggested Sample Queries for Evaluation

1. **Asset Root Cause Query:**
   > `"What causes seal leakage in pump P-101?"`
   *Expected:* Identifies `bearing wear` as the pre-determined root cause from KG, extracts vibration/temperature metrics, and cites `failure_log.txt`.

2. **Cross-Asset Isolation Query:**
   > `"What failed in C-201?"`
   *Expected:* Isolates compressor failure (`impeller fouling`) cleanly without pulling P-101 data.

3. **Hallucination Gate Test (Non-Existent Asset):**
   > `"What failed in V-999?"`
   *Expected:* Confidence gate evaluates score to `0.0` and triggers the safety refusal response.

4. **Procedural Query:**
   > `"What is the emergency shutdown procedure for the refinery?"`
   *Expected:* Returns procedural steps from `SOP_shutdown.pdf`.

---

## 📈 Development Phases Summary

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Project scaffold, multi-format loaders (PDF, Excel, OCR image, text, DOCX) | ✅ Complete |
| **Phase 2** | Chunking pipeline, regex asset extraction (`P-101`), metadata tagging | ✅ Complete |
| **Phase 3** | ChromaDB vector store, sentence-transformer embeddings, semantic search | ✅ Complete |
| **Phase 4** | Groq RAG answer engine, environment config, prompt engineering | ✅ Complete |
| **Phase 5** | Hybrid retrieval (KG + keyword + semantic), metadata boost, unified UI | ✅ Complete |
| **Phase 6** | Evidence-governed platform: confidence gate, asset filter, quotas, fact table, 12-test suite | ✅ Complete |

---

## 📄 License

Distributed under the MIT License.