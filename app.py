import os
import streamlit as st
from ingestion.loader import load_document

# Set page configuration with a premium title and layout
st.set_page_config(
    page_title="Knowledge Fabric - Ingestion Pipeline",
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
    <p>Phase 1 — Multiformat Document Ingestion Pipeline</p>
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
                st.sidebar.info("Cleared dev cache.")
else:
    st.sidebar.error("demo_docs/ directory not found.")

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
            
            # Extract attributes
            doc_type = doc['metadata']['type']
            char_count = len(doc['text'])
            preview_text = doc['text'][:1000]
            
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
            
            # Beautiful card presentation
            st.markdown(f"""
            <div class="doc-card-container" style="border: 1px solid rgba(255,255,255,0.08); border-radius:12px; padding:20px; background-color:#0f172a; margin-bottom:20px; box-shadow: 0 4px 20px rgba(0,0,0,0.15)">
                <div style="font-size:1.25rem; font-weight:600; margin-bottom:10px; color:#f8fafc; display:flex; justify-content:space-between; align-items:center;">
                    <span>🟢 {doc['source']} processed successfully</span>
                    <span style="background-color:rgba(255,255,255,0.05); padding:2px 8px; border-radius:4px; font-size:0.75rem; text-transform:uppercase; font-weight:bold; color:{badge_color}; border: 1px solid {badge_color}33;">{doc_type}</span>
                </div>
                <div style="display:flex; gap:20px; margin-bottom:15px; font-size:0.95rem; color:#94a3b8">
                    {meta_html}
                </div>
                <div style="font-size:0.75rem; color:#64748b; text-transform:uppercase; font-weight:700; margin-bottom:5px">Extracted Text Preview</div>
                <div style="background-color:#020617; border: 1px solid rgba(255,255,255,0.05); border-radius:6px; padding:12px; font-family:monospace; white-space:pre-wrap; max-height:250px; overflow-y:auto; font-size:0.85rem; color:#cbd5e1; text-align:left">{preview_text}</div>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Failed to process {os.path.basename(file_path)}: {str(e)}")
else:
    st.info("Upload documents or use the Developer Test Panel to load sample documents.")