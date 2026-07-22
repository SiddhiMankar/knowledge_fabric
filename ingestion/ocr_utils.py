import os
import shutil
import pytesseract
from PIL import Image, ImageOps

# Locate Tesseract on Windows if it is not in the system path
if not shutil.which("tesseract"):
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\Siddhi\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    ]
    for path in common_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break
else:
    # Explicitly set command path if default installation exists
    if os.path.exists(r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def ocr_image(image: Image.Image) -> str:
    """Extract text from a PIL image using Tesseract with pre-processing."""
    # Convert to grayscale
    image = ImageOps.grayscale(image)
    
    # Increase contrast
    image = ImageOps.autocontrast(image)
    
    # OCR with better settings:
    # --oem 3: Best OCR engine (LSTM)
    # --psm 6: Assume a single uniform block of text
    config = '--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=config)
    
    return text.strip()
