import fitz  # PyMuPDF
from pathlib import Path

def extract_text(file_path: Path, ext: str) -> str:
    ext = ext.lower().strip(".")
    if ext == "pdf":
        return extract_pdf_text(file_path)
    elif ext in {"png", "jpg", "jpeg"}:
        return "[OCR not implemented yet]"
    elif ext == "txt":
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")
    else:
        return "[Unsupported file type]"

def extract_pdf_text(file_path: Path) -> str:
    text = []
    doc = fitz.open(file_path)
    for page in doc:
        text.append(page.get_text())
    return "\n".join(text).strip()

def chunk_text(text: str, max_words: int = 200, overlap: int = 40) -> list:
    """Split text into overlapping word chunks"""
    words = text.split()
    chunks = []
    i = 0

    while i < len(words):
        chunk = words[i:i + max_words]
        chunks.append(" ".join(chunk))
        i += max_words - overlap  # Slide window
    return chunks
