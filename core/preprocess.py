import pymupdf4llm
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
import os
import platform
from typing import List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_poppler_path() -> Optional[str]:
    """Get the path to poppler binaries based on the operating system.
    
    Returns:
        Path to poppler binaries or None if not on Windows
    """
    if platform.system() == "Windows":
        return os.path.join(os.getcwd(), "poppler", "bin")
    return None

def extract_text(file_path: Path, ext: str) -> str:
    """Extract text from various file types.
    
    Args:
        file_path: Path to the file
        ext: File extension
        
    Returns:
        Extracted text content
    """
    ext = ext.lower().strip(".")
    try:
        if ext == "pdf":
            text = extract_pdf_text(file_path)
            # Fall back to OCR if text extraction yields minimal content
            if len(text.strip()) < 30:
                logger.info(f"Minimal text extracted from PDF, falling back to OCR: {file_path}")
                return extract_pdf_text_with_ocr(file_path)
            return text
        elif ext in {"png", "jpg", "jpeg"}:
            return extract_image_text(file_path)
        elif ext == "txt":
            return Path(file_path).read_text(encoding="utf-8", errors="ignore")
        else:
            return f"[Unsupported file type: {ext}]"
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        return f"[Error extracting text: {str(e)}]"

def extract_pdf_text(file_path: Path) -> str:
    """Extract text from PDF using pymupdf4llm.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    try:
        return pymupdf4llm.to_markdown(str(file_path))
    except Exception as e:
        logger.error(f"Error extracting PDF text: {str(e)}")
        return ""

def extract_pdf_text_with_ocr(file_path: Path) -> str:
    """Extract text from PDF using OCR as a fallback method.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    try:
        pages = convert_from_path(file_path, dpi=300, poppler_path=get_poppler_path())
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page)
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting PDF text with OCR: {str(e)}")
        return ""

def extract_image_text(file_path: Path) -> str:
    """Extract text from images using OCR.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Extracted text content
    """
    try:
        image = Image.open(file_path)
        return pytesseract.image_to_string(image).strip()
    except Exception as e:
        logger.error(f"Error extracting image text: {str(e)}")
        return ""

def chunk_text(text: str, max_words: int = 200, overlap: int = 40) -> List[str]:
    """Split text into overlapping word chunks for better semantic search.
    
    Args:
        text: Text to chunk
        max_words: Maximum words per chunk
        overlap: Number of overlapping words between chunks
        
    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return [""]
        
    words = text.split()
    chunks = []
    i = 0

    while i < len(words):
        chunk = words[i:i + max_words]
        chunks.append(" ".join(chunk))
        i += max_words - overlap  # Slide window with overlap
    
    return chunks