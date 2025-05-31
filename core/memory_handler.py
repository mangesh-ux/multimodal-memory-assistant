import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from core.preprocess import extract_text, chunk_text
from core.embedder import embed_and_store

MEMORY_INDEX_PATH = Path("data/memory_index.json")
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def get_file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()

import numpy as np

def sanitize_vector(v):
    if isinstance(v, np.ndarray):
        return v.tolist()
    elif isinstance(v, list):
        return [float(x) if isinstance(x, (np.float32, np.float64)) else x for x in v]
    return v


def save_uploaded_file(uploaded_file, title, tags, category, notes):
    file_bytes = uploaded_file.read()
    file_hash = get_file_hash(file_bytes)

    ext = Path(uploaded_file.name).suffix.lower().strip(".")
    filename = f"{file_hash}_{uploaded_file.name}"
    file_path = DATA_DIR / filename
    print("file_path", file_path)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Extract text
    try:
        text = extract_text(file_path, ext)
    except Exception as e:
        text = f"[Error extracting text: {e}]"

    raw_chunks = chunk_text(text)
    chunks = [{
        "text": c,
        "title": title or "",
        "tags": tags or [],
        "category": category or "",
        "notes": notes or "",
        "filename": uploaded_file.name,
        "date_uploaded": datetime.now().isoformat()
    } for c in raw_chunks]

    chunk_vectors = embed_and_store(chunks)


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
                            {"text": chunk, "vector": sanitize_vector(vec)}
                            for chunk, vec in zip(chunks, chunk_vectors)
                            ]

                            ,
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
