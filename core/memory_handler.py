import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from core.preprocess import extract_text, chunk_text
from core.embedder import embed_text_list

MEMORY_INDEX_PATH = Path("data/memory_index.json")
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def get_file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()

def save_uploaded_file(uploaded_file, title=None, tags=None, category=None, notes=None):
    file_bytes = uploaded_file.read()
    file_hash = get_file_hash(file_bytes)

    ext = Path(uploaded_file.name).suffix.lower().strip(".")
    filename = f"{file_hash}_{uploaded_file.name}"
    file_path = DATA_DIR / filename

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Extract text
    try:
        text = extract_text(file_path, ext)
    except Exception as e:
        text = f"[Error extracting text: {e}]"

    chunks = chunk_text(text)
    chunk_vectors = embed_text_list(chunks)

    # Load or create index
    if MEMORY_INDEX_PATH.exists():
        with open(MEMORY_INDEX_PATH, "r") as f:
            try:
                index = json.load(f)
            except json.JSONDecodeError:
                index = [] # If it's an empty file, this will work

    else:
        index = []

    # Create entry
    entry = {
        "filename": uploaded_file.name,
        "filetype": ext,
        "filepath": str(file_path),
        "text_preview": text[:500],
        "date_uploaded": datetime.now().isoformat(),
        "embedding_chunks": [
                            {"text": chunk, "vector": vec}
                            for chunk, vec in zip(chunks, chunk_vectors)
                            ],
        "source_hash": file_hash,
        "title": title or "",
        "tags": tags or [],
        "category": category or "",
        "notes": notes or ""
    }

    index.append(entry)

    with open(MEMORY_INDEX_PATH, "w") as f:
        json.dump(index, f, indent=2)

    return entry
