import os
import pytest
from ingestion.loader import load_document

# Define test cases for different document types
TEST_CASES = [
    ("demo_docs/pump_manual.pdf", "pdf", 2, None),
    ("demo_docs/inspection_report.jpg", "image", None, None),
    ("demo_docs/maintenance_history.xlsx", "excel", None, 2),
    ("demo_docs/failure_log.txt", "txt", None, None),
    ("demo_docs/shutdown_procedure.docx", "docx", None, None),
]

@pytest.mark.parametrize("file_path,expected_type,check_pages,check_sheets", TEST_CASES)
def test_ingestion_file(file_path, expected_type, check_pages, check_sheets):
    """End‑to‑end ingestion test for various document types.
    Verifies that load_document returns a correctly structured dictionary.
    """
    assert os.path.exists(file_path), f"File {file_path} does not exist"
    doc = load_document(file_path)

    # Basic schema checks
    for key in ("doc_id", "source", "text", "metadata"):
        assert key in doc, f"{key} missing in document"
    assert "type" in doc["metadata"], "metadata.type missing"

    # Content checks
    expected_doc_id = os.path.splitext(os.path.basename(file_path))[0]
    expected_source = os.path.basename(file_path)
    assert doc["doc_id"] == expected_doc_id, f"Expected doc_id {expected_doc_id}, got {doc['doc_id']}"
    assert doc["source"] == expected_source, f"Expected source {expected_source}, got {doc['source']}"
    assert doc["metadata"]["type"] == expected_type, f"Expected type {expected_type}, got {doc['metadata']['type']}"
    assert len(doc["text"]) >= 10, "Document text is too short"

    # Type‑specific metadata validation
    if expected_type == "pdf":
        assert "pages" in doc["metadata"], "pages metadata missing for pdf"
        if check_pages is not None:
            assert doc["metadata"]["pages"] == check_pages, f"Expected {check_pages} pages, got {doc['metadata']['pages']}"
    elif expected_type == "excel":
        assert "sheets" in doc["metadata"], "sheets metadata missing for excel"
        if check_sheets is not None:
            assert doc["metadata"]["sheets"] == check_sheets, f"Expected {check_sheets} sheets, got {doc['metadata']['sheets']}"
    else:
        assert "pages" not in doc["metadata"], f"pages metadata should not exist for type {expected_type}"
        assert "sheets" not in doc["metadata"], f"sheets metadata should not exist for type {expected_type}"
