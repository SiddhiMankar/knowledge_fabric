import os
import shutil
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = (
    r'C:\Program Files\Tesseract-OCR\tesseract.exe'
)
# If tesseract is not in PATH, try common locations on Windows
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

def load_image(file_path: str) -> dict:
    """
    Opens an image, extracts text using pytesseract OCR, and returns the stripped text.
    """
    with Image.open(file_path) as img:
        text = pytesseract.image_to_string(img)
    return {
        'text': text.strip()
    }
