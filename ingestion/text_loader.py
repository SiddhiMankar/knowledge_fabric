import os
import docx

def load_text(file_path: str) -> dict:
    """
    Loads text files (UTF-8 encoded) or DOCX files (by paragraph).
    """
    _, ext = os.path.splitext(file_path.lower())
    if ext == '.docx':
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs]
        extracted_text = "\n".join(paragraphs)
    else:
        # Default or .txt
        with open(file_path, 'r', encoding='utf-8') as f:
            extracted_text = f.read()
            
    return {
        'text': extracted_text
    }
