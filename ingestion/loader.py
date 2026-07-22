import os
from .pdf_loader import load_pdf
from .image_loader import load_image
from .excel_loader import load_excel
from .text_loader import load_text

SUPPORTED_EXTENSIONS = {
    '.pdf': 'pdf',
    '.png': 'image',
    '.jpg': 'image',
    '.jpeg': 'image',
    '.bmp': 'image',
    '.tif': 'image',
    '.tiff': 'image',
    '.xlsx': 'excel',
    '.xls': 'excel',
    '.txt': 'txt',
    '.docx': 'docx'
}

def load_document(file_path: str) -> dict:
    """
    Main router that detects the file extension and calls the correct loader.
    Converts the output into a canonical document object format.
    """
    filename = os.path.basename(file_path)
    doc_id, ext = os.path.splitext(filename)
    ext_lower = ext.lower()
    
    if ext_lower not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {ext}")
        
    doc_type = SUPPORTED_EXTENSIONS[ext_lower]
    
    pages_data = None
    if doc_type == 'pdf':
        res = load_pdf(file_path)
        metadata = {
            'type': 'pdf',
            'pages': res['pages']
        }
        text = res['text']
        pages_data = res['pages_data']
    elif doc_type == 'image':
        res = load_image(file_path)
        metadata = {
            'type': 'image'
        }
        text = res['text']
    elif doc_type == 'excel':
        res = load_excel(file_path)
        metadata = {
            'type': 'excel',
            'sheets': res['sheets']
        }
        text = res['text']
    elif doc_type == 'txt':
        res = load_text(file_path)
        metadata = {
            'type': 'txt'
        }
        text = res['text']
    elif doc_type == 'docx':
        res = load_text(file_path)
        metadata = {
            'type': 'docx'
        }
        text = res['text']
    else:
        raise ValueError(f"Unknown type mapping for extension: {ext}")
        
    doc_obj = {
        'doc_id': doc_id,
        'source': filename,
        'text': text,
        'metadata': metadata
    }
    if pages_data is not None:
        doc_obj['pages'] = pages_data
        
    return doc_obj
