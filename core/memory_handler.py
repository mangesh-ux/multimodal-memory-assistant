import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from core.preprocess import extract_text, chunk_text
from core.embedder import embed_and_store
from core.user_paths import (
    get_user_data_dir,
    get_memory_index_path
)
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# MEMORY_INDEX_PATH = Path("data/memory_index.json")
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

def auto_summarize(text: str, filename: str) -> str:
    if len(text.split()) < 200:
        return None  # skip short files

    prompt = (
        f"This is a document titled '{filename}'. "
        "Summarize it in 5-7 bullet points, preserving key insights, numbers, or tasks. "
        "Avoid fluff. Be factual and clear.\n\n"
        f"{text[:3000]}"  # trim to avoid token limit
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a concise and analytical summarization agent."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Summarization failed: {e}]"

def save_uploaded_file(uploaded_file, title, tags, category, notes, user_id, extracted_text):
    file_bytes = uploaded_file.read()
    file_hash = get_file_hash(file_bytes)

    ext = Path(uploaded_file.name).suffix.lower().strip(".")
    filename = f"{file_hash}_{uploaded_file.name}"
    file_path = get_user_data_dir(user_id) / filename
    print("file_path", file_path)
    with open(file_path, "wb") as f:
        f.write(file_bytes)


    raw_chunks = chunk_text(extracted_text)
    chunks = [{
        "text": c,
        "title": title or "",
        "tags": tags or [],
        "category": category or "",
        "notes": notes or "",
        "filename": uploaded_file.name,
        "date_uploaded": datetime.now().isoformat()
    } for c in raw_chunks]

    chunk_vectors = embed_and_store(chunks, user_id)

     # 🔍 Run summarizer agent if applicable
    summary = auto_summarize(extracted_text, uploaded_file.name)
    if summary:
        summary_chunks = [{
            "text": summary,
            "title": f"Summary of {title or uploaded_file.name}",
            "tags": tags + ["summary"],
            "category": category,
            "notes": "Auto-generated summary for this document.",
            "filename": uploaded_file.name,
            "date_uploaded": datetime.now().isoformat()
        }]
        embed_and_store(summary_chunks, user_id)


    # Load or create index
    if get_memory_index_path(user_id).exists():
        with open(get_memory_index_path(user_id), "r") as f:
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
        "text_preview": extracted_text[:500],
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

    with open(get_memory_index_path(user_id), "w") as f:
        json.dump(index, f, indent=2)

    return entry, summary
