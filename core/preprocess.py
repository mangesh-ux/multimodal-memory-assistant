import pymupdf4llm
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
import os
import platform

def get_poppler_path():
    if platform.system() == "Windows":
        return os.path.join(os.getcwd(), "poppler", "bin")
    return None

def extract_text(file_path: Path, ext: str) -> str:
    ext = ext.lower().strip(".")
    if ext == "pdf":
        text = extract_pdf_text(file_path)
        if len(text.strip()) < 30:
            return extract_pdf_text_with_ocr(file_path)
        return text
    elif ext in {"png", "jpg", "jpeg"}:
        return extract_image_text(file_path)
    elif ext == "txt":
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")
    else:
        return "[Unsupported file type]"

def extract_pdf_text(file_path: Path) -> str:
    return pymupdf4llm.to_markdown(str(file_path))

def extract_pdf_text_with_ocr(file_path: Path) -> str:
    pages = convert_from_path(file_path, dpi=300, poppler_path=get_poppler_path())
    text = ""
    for page in pages:
        text += pytesseract.image_to_string(page)
    return text.strip()

def extract_image_text(file_path: Path) -> str:
    image = Image.open(file_path)
    return pytesseract.image_to_string(image).strip()

def chunk_text(text: str, max_words: int = 200, overlap: int = 40) -> list:
    "Split text into overlapping word chunks"
    words = text.split()
    chunks = []
    i = 0

    while i < len(words):
        chunk = words[i:i + max_words]
        chunks.append(" ".join(chunk))
        i += max_words - overlap  # Slide window
    return chunks