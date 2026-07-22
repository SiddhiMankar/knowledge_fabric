import os
import sys
import json
from ingestion.loader import load_document
from processing.chunker import chunk_document, save_chunks

def verify_chunking():
    # Remove previous chunks file to start fresh
    output_path = 'data/processed/chunks.json'
    if os.path.exists(output_path):
        os.remove(output_path)
        
    print("--- Running Chunking E2E Validation ---")
    
    # 1. Load and chunk PDF (pump_manual.pdf)
    doc_pdf = load_document("demo_docs/pump_manual.pdf")
    chunks_pdf = chunk_document(doc_pdf)
    
    print(f"PDF Chunks generated: {len(chunks_pdf)}")
    for c in chunks_pdf:
        print(f"  Chunk: {c['chunk_id']}, Word Count: {len(c['text'].split())}, Assets: {c['metadata']['asset_ids']}")
        
    # Check page-boundary and multi-chunk requirements
    # page 1 has 800 words + title words. It should produce exactly 2 chunks.
    # page 2 has ~15 words. It should produce exactly 1 chunk.
    # Total chunks for PDF should be 3.
    assert len(chunks_pdf) == 3, f"Expected 3 chunks for PDF, got {len(chunks_pdf)}"
    
    # Check chunk IDs
    assert chunks_pdf[0]['chunk_id'] == 'pump_manual_p1_c1', f"Unexpected chunk_id: {chunks_pdf[0]['chunk_id']}"
    assert chunks_pdf[1]['chunk_id'] == 'pump_manual_p1_c2', f"Unexpected chunk_id: {chunks_pdf[1]['chunk_id']}"
    assert chunks_pdf[2]['chunk_id'] == 'pump_manual_p2_c1', f"Unexpected chunk_id: {chunks_pdf[2]['chunk_id']}"
    
    # Check word counts
    # The first chunk on page 1 must be exactly 600 words (or 600 + title words)
    c1_words = chunks_pdf[0]['text'].split()
    c2_words = chunks_pdf[1]['text'].split()
    assert 500 <= len(c1_words) <= 700, f"Chunk 1 size {len(c1_words)} is out of bounds (500-700)"
    
    # Check overlap of adjacent chunks on the same page
    # Overlap target is 90 words. In our implementation, step = 510.
    # So chunk 2 starts at index 510 of the word list.
    # Let's verify that the first 90 words of chunk 2 match the words in chunk 1 starting at index 510.
    overlap_words_c1 = c1_words[510:600]
    overlap_words_c2 = c2_words[:90]
    assert len(overlap_words_c1) == len(overlap_words_c2), "Overlap sizes do not match"
    assert overlap_words_c1 == overlap_words_c2, f"Overlap words do not match!\nC1: {overlap_words_c1[:5]}...\nC2: {overlap_words_c2[:5]}..."
    print("SUCCESS: Adjacent chunks overlap matches exactly!")
    
    # Check asset detection
    # Chunk 1 (words 0 to 600) contains P-101 (word index 100) and V-200 (word index 400).
    # Chunk 2 (words 510 to 800) contains V-200 (word index 400 - wait, no! 400 is not in range [510, 800].
    # Word index 400 is NOT in chunk 2. So chunk 2 contains B-3 (word index 700). Let's check.)
    print(f"Chunk 1 asset_ids: {chunks_pdf[0]['metadata']['asset_ids']}")
    print(f"Chunk 2 asset_ids: {chunks_pdf[1]['metadata']['asset_ids']}")
    print(f"Chunk 3 asset_ids: {chunks_pdf[2]['metadata']['asset_ids']}")
    
    assert 'P-101' in chunks_pdf[0]['metadata']['asset_ids'], "P-101 missing from Chunk 1"
    assert 'V-200' in chunks_pdf[0]['metadata']['asset_ids'], "V-200 missing from Chunk 1"
    assert 'B-3' in chunks_pdf[1]['metadata']['asset_ids'], "B-3 missing from Chunk 2"
    # Page 2 has V-101 and C-12
    assert 'V-101' in chunks_pdf[2]['metadata']['asset_ids'], "V-101 missing from Chunk 3"
    assert 'C-12' in chunks_pdf[2]['metadata']['asset_ids'], "C-12 missing from Chunk 3"
    print("SUCCESS: Asset ID regex-based detection is correct!")
    
    # 2. Save PDF chunks and check file creation
    all_chunks = save_chunks(chunks_pdf)
    assert os.path.exists(output_path), "chunks.json not created"
    
    with open(output_path, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    assert len(saved_data) == 3, f"Expected 3 saved chunks, got {len(saved_data)}"
    
    # 3. Load, chunk and save other files to check cumulative updates
    for filename in ["maintenance_history.xlsx", "inspection_report.jpg", "failure_log.txt", "shutdown_procedure.docx"]:
        doc = load_document(os.path.join("demo_docs", filename))
        chunks = chunk_document(doc)
        all_chunks = save_chunks(chunks)
        
    # Total chunks in json should be:
    # pdf: 3 chunks
    # excel: 1 chunk
    # image: 1 chunk
    # txt: 1 chunk
    # docx: 1 chunk
    # Total: 7 chunks
    with open(output_path, 'r', encoding='utf-8') as f:
        final_saved_data = json.load(f)
        
    print(f"Total cumulative chunks in database: {len(final_saved_data)}")
    assert len(final_saved_data) == 7, f"Expected 7 total chunks, got {len(final_saved_data)}"
    
    # Check that all chunk IDs are unique
    chunk_ids = [c['chunk_id'] for c in final_saved_data]
    assert len(chunk_ids) == len(set(chunk_ids)), "Duplicate chunk IDs found!"
    print("SUCCESS: All chunk IDs are unique!")
    
    print("\n--- All Chunking assertions passed successfully! ---")
    sys.exit(0)

if __name__ == "__main__":
    verify_chunking()
