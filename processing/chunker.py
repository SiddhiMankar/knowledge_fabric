import os
import re
import json

ASSET_PATTERN = r'PUMP-\d+|P-\d+|V-\d+|C-\d+|B-\d+'

def chunk_document(document: dict) -> list:
    """
    Transforms the raw extracted document text into retrieval-ready chunks
    and attaches standardized metadata.
    
    Chunking Rules:
    - Word-based chunking.
    - Chunk size: 600 words target (range 500-700).
    - Overlap: 90 words target (range 80-100).
    - Page boundary preservation: PDF pages are chunked independently.
    """
    source = document['source']
    doc_type = document['metadata']['type']
    
    # Generate base name for chunk ID: lowercase, spaces replaced with underscores, extensions stripped
    base_name = source
    extensions_to_strip = ['.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.xlsx', '.xls', '.txt', '.docx']
    for ext in extensions_to_strip:
        base_name = base_name.replace(ext, '').replace(ext.upper(), '')
    base_name = base_name.lower().replace(' ', '_')
    
    chunks = []
    
    # Identify pages to process
    if doc_type == 'pdf' and 'pages' in document:
        pages_data = document['pages']
    else:
        # Non-PDF or PDF page-wise not available
        pages_data = [{'page': 1, 'text': document['text']}]
        
    chunk_size = 600
    overlap = 90
    step = chunk_size - overlap
    
    for page_item in pages_data:
        page_number = page_item['page']
        page_text = page_item['text']
        
        words = page_text.split()
        if not words:
            continue
            
        chunk_index = 1
        num_words = len(words)
        
        # Use range with step to create overlapping windows
        for start in range(0, num_words, step):
            chunk_words = words[start:start + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            # Skip empty chunks
            if not chunk_text.strip():
                continue
                
            # Chunk ID format: {document_name}_p{page}_c{chunk_number}
            chunk_id = f'{base_name}_p{page_number}_c{chunk_index}'
            
            # Asset ID detection
            raw_asset_ids = re.findall(ASSET_PATTERN, chunk_text, flags=re.IGNORECASE)
            # Normalize to uppercase and deduplicate, then sort
            asset_ids = sorted(list(set(aid.upper() for aid in raw_asset_ids)))
            
            chunk_obj = {
                'chunk_id': chunk_id,
                'text': chunk_text,
                'metadata': {
                    'source': source,
                    'page': page_number,
                    'asset_ids': asset_ids
                }
            }
            chunks.append(chunk_obj)
            chunk_index += 1
            
    return chunks

def save_chunks(new_chunks: list, output_path: str = 'data/processed/chunks.json') -> list:
    """
    Saves chunks to a JSON file. Automatically merges with existing chunks,
    overwriting chunks for the same source file to avoid duplication.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    existing_chunks = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_chunks = json.load(f)
        except Exception:
            existing_chunks = []
            
    # Filter out existing chunks that have the same source as any incoming new chunks
    new_sources = {chunk['metadata']['source'] for chunk in new_chunks}
    filtered_chunks = [c for c in existing_chunks if c['metadata']['source'] not in new_sources]
    
    # Combine
    combined_chunks = filtered_chunks + new_chunks
    
    # Write back to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined_chunks, f, indent=2, ensure_ascii=False)
        
    # Automatically sync with ChromaDB vector store
    try:
        from retrieval.vector_store import index_chunks
        print("Syncing ChromaDB vector store with updated chunks...")
        index_chunks(output_path)
    except Exception as e:
        print(f"Warning: Failed to automatically sync ChromaDB: {e}")
        
    return combined_chunks

