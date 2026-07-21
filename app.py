import streamlit as st

st.set_page_config(page_title="Knowledge Fabric")

st.title("Knowledge Fabric")
st.write("Phase 0 is working!")

uploaded_file = st.file_uploader(
    "Upload a PDF",
    type=["pdf"]
)

if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")