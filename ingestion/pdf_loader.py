import fitz  # PyMuPDF

def load_pdf(file_path: str) -> dict:
    """
    Opens a PDF file, extracts text from all pages, and returns a dictionary
    with the combined text and the page count.
    """
    doc = fitz.open(file_path)
    text_parts = []
    
    # Use doc.pages() generator if available, fallback to iterating doc
    pages_iterable = doc.pages() if hasattr(doc, 'pages') else doc
    for page in pages_iterable:
        text_parts.append(page.get_text())
        
    full_text = "\n".join(text_parts)
    return {
        'text': full_text,
        'pages': len(doc)
    }
