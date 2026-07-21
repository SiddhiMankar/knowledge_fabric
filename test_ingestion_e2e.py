import os
import sys
from ingestion.loader import load_document

def test_file(file_path, expected_type, check_pages=None, check_sheets=None, min_text_len=10):
    print(f"\n--- Testing: {file_path} ---")
    if not os.path.exists(file_path):
        print(f"ERROR: File {file_path} does not exist!")
        return False
        
    try:
        doc = load_document(file_path)
        
        # Verify schema keys
        assert 'doc_id' in doc, "doc_id missing"
        assert 'source' in doc, "source missing"
        assert 'text' in doc, "text missing"
        assert 'metadata' in doc, "metadata missing"
        assert 'type' in doc['metadata'], "metadata.type missing"
        
        # Verify contents
        expected_doc_id = os.path.splitext(os.path.basename(file_path))[0]
        expected_source = os.path.basename(file_path)
        
        assert doc['doc_id'] == expected_doc_id, f"Expected doc_id {expected_doc_id}, got {doc['doc_id']}"
        assert doc['source'] == expected_source, f"Expected source {expected_source}, got {doc['source']}"
        assert doc['metadata']['type'] == expected_type, f"Expected type {expected_type}, got {doc['metadata']['type']}"
        assert len(doc['text']) >= min_text_len, f"Text length too short ({len(doc['text'])})"
        
        if expected_type == 'pdf':
            assert 'pages' in doc['metadata'], "pages metadata missing for pdf"
            if check_pages is not None:
                assert doc['metadata']['pages'] == check_pages, f"Expected {check_pages} pages, got {doc['metadata']['pages']}"
                
        elif expected_type == 'excel':
            assert 'sheets' in doc['metadata'], "sheets metadata missing for excel"
            if check_sheets is not None:
                assert doc['metadata']['sheets'] == check_sheets, f"Expected {check_sheets} sheets, got {doc['metadata']['sheets']}"
                
        else:
            assert 'pages' not in doc['metadata'], f"pages metadata should not exist for type {expected_type}"
            assert 'sheets' not in doc['metadata'], f"sheets metadata should not exist for type {expected_type}"
            
        print(f"SUCCESS: {file_path} parsed correctly.")
        print(f"Metadata: {doc['metadata']}")
        print(f"Text Preview (first 100 chars): {repr(doc['text'][:100])}")
        return True
    except Exception as e:
        print(f"FAILED: {file_path} failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = True
    
    # PDF Test
    success &= test_file("demo_docs/pump_manual.pdf", "pdf", check_pages=2)
    
    # Image OCR Test
    success &= test_file("demo_docs/inspection_report.jpg", "image")
    
    # Excel Test
    success &= test_file("demo_docs/maintenance_history.xlsx", "excel", check_sheets=2)
    
    # Text Test
    success &= test_file("demo_docs/failure_log.txt", "txt")
    
    # Docx Test
    success &= test_file("demo_docs/shutdown_procedure.docx", "docx")
    
    if success:
        print("\nAll tests passed successfully! e2e pipeline is working.")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
