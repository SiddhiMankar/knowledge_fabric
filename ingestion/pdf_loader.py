import fitz  # PyMuPDF
from PIL import Image
from ingestion.ocr_utils import ocr_image

def load_pdf(file_path: str) -> dict:
    """
    Opens a PDF file, extracts text from all pages (with OCR fallback for scanned pages),
    and returns a dictionary with the combined text, page count, and page-wise data.
    """
    doc = fitz.open(file_path)
    text_parts = []
    pages_data = []
    
    # Use doc.pages() generator if available, fallback to iterating doc
    pages_iterable = doc.pages() if hasattr(doc, 'pages') else doc
    for i, page in enumerate(pages_iterable, start=1):
        # Step 3A: Try normal text extraction
        page_text = page.get_text().strip()
        
        # Step 3B: If text is too small, use OCR
        if len(page_text) < 50:
            print(f"[OCR] Page {i}: text too small ({len(page_text)} chars), running OCR...")
            
            # Render page as high-resolution image
            pix = page.get_pixmap(dpi=300)
            image = Image.frombytes(
                'RGB',
                [pix.width, pix.height],
                pix.samples
            )
            
            # OCR the image
            page_text = ocr_image(image)
            print(f"[OCR] Page {i}: extracted {len(page_text)} characters")
            
            # Step 10: Add a safety check for blank pages
            if len(page_text.strip()) < 10:
                print(f"[WARN] Page {i}: OCR produced almost no text")
                
        text_parts.append(page_text)
        pages_data.append({
            'page': i,
            'text': page_text
        })
        
    full_text = "\n".join(text_parts)
    return {
        'text': full_text,
        'pages': len(doc),
        'pages_data': pages_data
    }
