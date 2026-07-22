import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables from .env file
load_dotenv()

from ingestion.loader import load_document
from processing.chunker import chunk_document, save_chunks
from retrieval.vector_store import search, index_chunks

# Set page configuration with a premium title and layout
st.set_page_config(
    page_title="Knowledge Fabric - Knowledge Platform",
    page_icon="⚙️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Inject custom CSS for premium design (fonts, colors, and layout)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
}

.title-card {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 30px;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px 0 rgba(31, 38, 135, 0.1);
    text-align: center;
}

.title-card h1 {
    margin: 0;
    font-size: 2.8rem;
    background: linear-gradient(90deg, #a78bfa 0%, #818cf8 50%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
}

.title-card p {
    color: #94a3b8;
    margin-top: 10px;
    margin-bottom: 0;
    font-size: 1.15rem;
}

.section-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.4rem;
    font-weight: 600;
    margin-top: 20px;
    margin-bottom: 15px;
    color: #f1f5f9;
}
</style>
""", unsafe_allow_html=True)

# Ensure temp directories exist
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

# Title block
st.markdown("""
<div class="title-card">
    <h1>Knowledge Fabric</h1>
    <p>Multi-Format Ingestion & Semantic Search Platform</p>
</div>
""", unsafe_allow_html=True)

# Initialize dev loaded files session state
if 'dev_loaded_files' not in st.session_state:
    st.session_state.dev_loaded_files = []

# Sidebar Developer panel to bypass browser headless upload limits
st.sidebar.markdown("### 🛠️ Developer Test Panel")
st.sidebar.info("Headless browser agents cannot easily trigger native file upload dialogs. Use this panel to select and process demo files directly from disk.")

demo_dir = "demo_docs"
if os.path.exists(demo_dir):
    demo_files = [f for f in os.listdir(demo_dir) if os.path.isfile(os.path.join(demo_dir, f))]
    selected_demo = st.sidebar.selectbox("Select Demo Document", ["Choose a file..."] + sorted(demo_files))
    
    if selected_demo != "Choose a file...":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.sidebar.button("Ingest File", use_container_width=True):
                demo_path = os.path.join(demo_dir, selected_demo)
                if demo_path not in st.session_state.dev_loaded_files:
                    st.session_state.dev_loaded_files.append(demo_path)
                    st.sidebar.success(f"Added {selected_demo}!")
        with col2:
            if st.sidebar.button("Clear All", use_container_width=True):
                st.session_state.dev_loaded_files = []
                # Clear chunks file
                chunks_file = 'data/processed/chunks.json'
                if os.path.exists(chunks_file):
                    os.remove(chunks_file)
                st.sidebar.info("Cleared dev cache & chunks.json.")
else:
    st.sidebar.error("demo_docs/ directory not found.")

# Create tabs for Ingestion and Search
tab1, tab2 = st.tabs(["📂 Document Ingestion & Chunking", "🔍 Semantic Search Engine"])

with tab1:
    # Uploader Section
    st.markdown('<div class="section-title">📂 Document Ingestion</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload files (PDF, images, Excel, TXT, DOCX)",
        type=["pdf", "png", "jpg", "jpeg", "bmp", "tif", "xlsx", "xls", "txt", "docx"],
        accept_multiple_files=True
    )
    
    # Collect all files to process (both uploaded and developer loaded)
    files_to_process = []
    
    # Process uploaded files
    if uploaded_files:
        for uploaded_file in uploaded_files:
            raw_path = os.path.join("data/raw", uploaded_file.name)
            with open(raw_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            files_to_process.append(raw_path)
            
    # Process developer loaded files
    for dev_file in st.session_state.dev_loaded_files:
        if os.path.exists(dev_file) and dev_file not in files_to_process:
            files_to_process.append(dev_file)
            
    if files_to_process:
        st.markdown('<div class="section-title">⚙️ Processing Logs</div>', unsafe_allow_html=True)
        
        for file_path in files_to_process:
            try:
                # Process using router
                doc = load_document(file_path)
                
                # Generate retrieval-ready chunks (triggers auto-indexing in save_chunks)
                chunks = chunk_document(doc)
                
                # Save chunks to database
                cumulative_chunks = save_chunks(chunks)
                total_cumulative_count = len(cumulative_chunks)
                
                # Extract attributes
                doc_type = doc['metadata']['type']
                char_count = len(doc['text'])
                
                num_chunks = len(chunks)
                first_chunk_id = chunks[0]['chunk_id'] if chunks else "N/A"
                first_chunk_assets = ", ".join(chunks[0]['metadata']['asset_ids']) if chunks and chunks[0]['metadata']['asset_ids'] else "None"
                first_chunk_text = chunks[0]['text'][:800] if chunks else ""
                
                # Format badge color dynamically
                badge_color = "#94a3b8"
                if doc_type == "pdf":
                    badge_color = "#f87171"
                elif doc_type == "image":
                    badge_color = "#c084fc"
                elif doc_type == "excel":
                    badge_color = "#34d399"
                elif doc_type == "docx":
                    badge_color = "#60a5fa"
                elif doc_type == "txt":
                    badge_color = "#38bdf8"
                    
                # Build metadata strings for standard textual presentation
                meta_html = f"<div><strong>Type:</strong> <span style='color:{badge_color}'>{doc_type}</span></div>"
                if "pages" in doc['metadata']:
                    meta_html += f"<div><strong>Pages:</strong> {doc['metadata']['pages']}</div>"
                if "sheets" in doc['metadata']:
                    meta_html += f"<div><strong>Sheets:</strong> {doc['metadata']['sheets']}</div>"
                meta_html += f"<div><strong>Characters:</strong> {char_count:,}</div>"
                meta_html += f"<div><strong>Chunks:</strong> {num_chunks}</div>"
                meta_html += f"<div><strong>First Chunk ID:</strong> <span style='font-family:monospace; color:#cbd5e1;'>{first_chunk_id}</span></div>"
                meta_html += f"<div><strong>Assets:</strong> <span style='color:#e2e8f0; font-weight:600;'>{first_chunk_assets}</span></div>"
                meta_html += f"<div><strong>Total Cumulative Chunks:</strong> {total_cumulative_count}</div>"
                
                # Beautiful card presentation
                st.markdown(f"""
                <div class="doc-card-container" style="border: 1px solid rgba(255,255,255,0.08); border-radius:12px; padding:20px; background-color:#0f172a; margin-bottom:20px; box-shadow: 0 4px 20px rgba(0,0,0,0.15)">
                    <div style="font-size:1.25rem; font-weight:600; margin-bottom:10px; color:#f8fafc; display:flex; justify-content:space-between; align-items:center;">
                        <span>🟢 {doc['source']} processed successfully</span>
                        <span style="background-color:rgba(255,255,255,0.05); padding:2px 8px; border-radius:4px; font-size:0.75rem; text-transform:uppercase; font-weight:bold; color:{badge_color}; border: 1px solid {badge_color}33;">{doc_type}</span>
                    </div>
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:10px; margin-bottom:15px; font-size:0.95rem; color:#94a3b8">
                        {meta_html}
                    </div>
                    <div style="font-size:0.75rem; color:#64748b; text-transform:uppercase; font-weight:700; margin-bottom:5px">First Chunk Text Preview ({first_chunk_id})</div>
                    <div style="background-color:#020617; border: 1px solid rgba(255,255,255,0.05); border-radius:6px; padding:12px; font-family:monospace; white-space:pre-wrap; max-height:250px; overflow-y:auto; font-size:0.85rem; color:#cbd5e1; text-align:left">{first_chunk_text}</div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Failed to process {os.path.basename(file_path)}: {str(e)}")
                import traceback
                st.sidebar.code(traceback.format_exc())
    else:
        st.info("Upload documents or use the Developer Test Panel to load sample documents.")

with tab2:
    st.markdown('<div class="section-title">🔍 Semantic Query Interface</div>', unsafe_allow_html=True)
    
    query = st.text_input(
        "Ask a question or enter query terms:",
        value="What causes seal leakage in pump P-101?",
        placeholder="e.g. What causes seal leakage in pump P-101?"
    )
    
    col1, col2 = st.columns([3, 1])
    with col2:
        top_k = st.slider("Results (k)", min_value=1, max_value=10, value=3)
    with col1:
        st.write("")  # Alignment spacing
        st.write("")
        search_clicked = st.button("Search Knowledge Base", use_container_width=True, type="primary")
        
    if search_clicked or query:
        if query.strip():
            with st.spinner("Searching vector database..."):
                try:
                    # Load all chunks for keyword search
                    import json
                    all_chunks = []
                    chunks_file = 'data/processed/chunks.json'
                    if os.path.exists(chunks_file):
                        with open(chunks_file, 'r', encoding='utf-8') as f:
                            try:
                                all_chunks = json.load(f)
                            except Exception:
                                pass

                    from retrieval.hybrid import hybrid_retrieve
                    # Evidence-governed hybrid retrieval
                    hybrid_results = hybrid_retrieve(query, all_chunks, top_k=top_k)
                    trace = hybrid_results.get('trace', {})
                    retrieval_confidence = trace.get('retrieval_confidence', 0.0)

                    # Convert boosted/filtered vector results to format expected by generate_answer
                    boosted_docs = [r['text'] for r in hybrid_results['vector_results']]
                    boosted_metas = [r['metadata'] for r in hybrid_results['vector_results']]
                    boosted_results = {
                        'documents': [boosted_docs],
                        'metadatas': [boosted_metas]
                    }

                    if boosted_docs or hybrid_results.get('keyword_results'):
                        # --- RAG Answer ---
                        st.markdown('<div class="section-title">🤖 AI Assistant Response</div>', unsafe_allow_html=True)
                        try:
                            from retrieval.rag import generate_answer
                            rag_response = generate_answer(query, boosted_results, confidence=retrieval_confidence)

                            # Root cause source badge
                            rc_source = rag_response.get('root_cause_source')
                            rc_conf   = rag_response.get('root_cause_confidence')
                            rc_name   = rag_response.get('root_cause')

                            if rc_source == 'knowledge_graph' and rc_name:
                                rc_badge_html = f"""
                                <div style="display:flex; align-items:center; gap:10px; margin-bottom:14px; flex-wrap:wrap;">
                                    <span style="background:rgba(59,130,246,0.12); color:#60a5fa; border:1px solid rgba(59,130,246,0.3); padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:700;">
                                        🕸️ Root cause source: Knowledge Graph
                                    </span>
                                    <span style="background:rgba(52,211,153,0.1); color:#34d399; border:1px solid rgba(52,211,153,0.25); padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:700;">
                                        ✅ {rc_name} &nbsp;·&nbsp; confidence {rc_conf}
                                    </span>
                                    <span style="background:rgba(168,85,247,0.1); color:#c084fc; border:1px solid rgba(168,85,247,0.2); padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:700;">
                                        📊 Retrieval confidence: {retrieval_confidence}
                                    </span>
                                </div>"""
                            elif rc_source == 'insufficient_evidence':
                                rc_badge_html = f"""
                                <div style="margin-bottom:14px;">
                                    <span style="background:rgba(239,68,68,0.1); color:#f87171; border:1px solid rgba(239,68,68,0.25); padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:700;">
                                        ⚠️ Insufficient evidence · confidence {retrieval_confidence}
                                    </span>
                                </div>"""
                            else:
                                rc_badge_html = ""

                            st.markdown(f"""
                            <div class="rag-card" style="border: 1px solid rgba(168, 85, 247, 0.2); border-radius:12px; padding:20px; background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(168, 85, 247, 0.08) 100%); margin-bottom:25px; box-shadow: 0 4px 20px rgba(168, 85, 247, 0.05)">
                                <div style="font-size:1.15rem; font-weight:600; color:#f8fafc; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
                                    <span>✨ Synthesized Answer</span>
                                    <span style="background-color:rgba(168, 85, 247, 0.1); color:#c084fc; border: 1px solid rgba(168, 85, 247, 0.2); padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:bold;">RAG Engine</span>
                                </div>
                                {rc_badge_html}
                                <div style="font-family:sans-serif; font-size:0.95rem; color:#e2e8f0; line-height:1.6; white-space:pre-wrap; text-align:left;">{rag_response['answer']}</div>
                                <div style="margin-top:15px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.06); font-size:0.8rem; color:#94a3b8;">
                                    <strong>Consulted Sources:</strong> {", ".join(rag_response['sources'])}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        except Exception as re:
                            st.error(f"RAG generation failed: {re}")

                        # --- Knowledge Graph Relations ---
                        if hybrid_results.get('graph_results'):
                            st.markdown('### 🕸️ Knowledge Graph Relations')
                            graph_html = '<div style="display:flex; flex-wrap:wrap; gap:10px; margin-bottom:25px;">'
                            for g in hybrid_results['graph_results']:
                                relation = g['relation']
                                entity   = g['entity']
                                graph_html += f"""
                                <span style="background-color:rgba(59, 130, 246, 0.1); color:#60a5fa; border: 1px solid rgba(59, 130, 246, 0.2); padding:6px 14px; border-radius:20px; font-size:0.85rem; font-weight:600;">
                                    ⛓️ {relation} ➔ <span style="color:#f8fafc;">{entity}</span>
                                </span>
                                """
                            graph_html += '</div>'
                            st.markdown(graph_html, unsafe_allow_html=True)

                        # --- Unified Evidence List ---
                        st.markdown(f"### 🗃️ Unified Evidence List ({len(hybrid_results['merged_results'])} items found):")

                        for i, r in enumerate(hybrid_results['merged_results']):
                            r_type = r['retrieval_type']
                            source = r['metadata'].get('source', 'Unknown')
                            page   = r['metadata'].get('page', 'Unknown')
                            assets = r['metadata'].get('asset_ids', 'None')
                            text   = r['text']

                            if r_type == 'semantic':
                                badge_text   = "Semantic Match"
                                badge_bg     = "rgba(52, 211, 153, 0.1)"
                                badge_color  = "#34d399"
                                border_color = "rgba(52, 211, 153, 0.15)"
                                score_val    = r.get('score', 0.0)
                                score_text   = f"{max(0.0, min(100.0, score_val * 100.0)):.1f}% Match"
                            elif r_type == 'keyword':
                                badge_text   = "Keyword Match"
                                badge_bg     = "rgba(245, 158, 11, 0.1)"
                                badge_color  = "#f59e0b"
                                border_color = "rgba(245, 158, 11, 0.15)"
                                score_text   = "Asset Tag Match"
                            else:
                                badge_text   = "Graph Relation"
                                badge_bg     = "rgba(59, 130, 246, 0.1)"
                                badge_color  = "#3b82f6"
                                border_color = "rgba(59, 130, 246, 0.15)"
                                score_text   = "KG Lookup"

                            source_color = "#38bdf8"
                            if source.endswith(".pdf"):
                                source_color = "#f87171"
                            elif source.endswith((".xlsx", ".xls")):
                                source_color = "#34d399"
                            elif source.endswith(".docx"):
                                source_color = "#60a5fa"
                            elif source == "knowledge_graph":
                                source_color = "#a78bfa"

                            st.markdown(f"""
                            <div class="result-card" style="border: 1px solid {border_color}; border-radius:12px; padding:20px; background-color:#0f172a; margin-bottom:15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1)">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                                    <div style="font-size:1.05rem; font-weight:600; color:#f8fafc;">
                                        Evidence {i+1} <span style="background-color:{badge_bg}; color:{badge_color}; border: 1px solid {badge_color}33; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:bold; margin-left:8px; text-transform:uppercase;">{badge_text}</span>
                                    </div>
                                    <span style="font-size:0.8rem; font-weight:600; color:#94a3b8;">{score_text}</span>
                                </div>
                                <div style="display:flex; flex-wrap:wrap; gap:12px; margin-bottom:12px; font-size:0.85rem; color:#94a3b8;">
                                    <div><strong>Source:</strong> <span style="color:{source_color};">{source}</span></div>
                                    {"<div><strong>Page:</strong> <span style='color:#cbd5e1;'>" + str(page) + "</span></div>" if r_type != "graph" else ""}
                                    {"<div><strong>Assets:</strong> <span style='color:#cbd5e1; font-weight:600;'>" + str(assets) + "</span></div>" if r_type != "graph" else ""}
                                </div>
                                <div style="background-color:#020617; border: 1px solid rgba(255,255,255,0.04); border-radius:6px; padding:12px; font-family:sans-serif; font-size:0.92rem; color:#cbd5e1; line-height:1.5; text-align:left;">
                                    {text}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        # --- Retrieval Trace Expander ---
                        with st.expander("🔍 Evidence Selection Trace", expanded=False):
                            t = hybrid_results.get('trace', {})
                            st.markdown(f"""
                            <div style="font-family:monospace; font-size:0.88rem; color:#94a3b8; line-height:2;">
                                <div>📌 <strong>Query assets:</strong> <span style="color:#60a5fa;">{', '.join(t.get('query_assets', [])) or 'None (generic query)'}</span></div>
                                <div>📦 <strong>Vector candidates:</strong> {t.get('vector_candidates', 0)}</div>
                                <div>🚫 <strong>Filtered out (asset mismatch):</strong> {t.get('filtered_out_asset_mismatch', 0)}</div>
                                <div>🕸️ <strong>KG relations used:</strong> {t.get('kg_relations_used', 0)}</div>
                                <div>📊 <strong>Doc-type quotas applied:</strong> {t.get('evidence_quotas_applied', {})}</div>
                                <div>📁 <strong>Final evidence sources:</strong> <span style="color:#34d399;">{', '.join(t.get('final_evidence', [])) or 'None'}</span></div>
                                <div>🎯 <strong>Retrieval confidence:</strong> <span style="color:{'#34d399' if t.get('retrieval_confidence',0) >= 0.5 else '#f87171'}; font-weight:bold;">{t.get('retrieval_confidence', 0.0)}</span></div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No matching chunks found in the database. Try re-indexing or asking a different question.")
                except Exception as e:
                    st.error(f"Search failed: {e}")
                    st.exception(e)
                    
    st.markdown("---")
    st.markdown("### 🔄 Index Management")
    if st.button("Force Re-index Vector Store", use_container_width=True):
        with st.spinner("Re-indexing chunks into ChromaDB..."):
            try:
                count = index_chunks()
                st.success(f"Successfully re-indexed {count} chunks in ChromaDB!")
            except Exception as e:
                st.error(f"Re-indexing failed: {e}")