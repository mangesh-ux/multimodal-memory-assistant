import json
import numpy as np
from pathlib import Path
from core.embedder import embed_text_list

MEMORY_INDEX_PATH = Path("data/memory_index.json")

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def retrieve_relevant_chunks(query: str, top_k: int = 5) -> list[dict]:
    # Step 1: Embed the question
    query_vector = embed_text_list([query])[0]

    # Step 2: Load memory
    with open(MEMORY_INDEX_PATH, "r") as f:
        index = json.load(f)

    scored_chunks = []
    for entry in index:
        for chunk in entry["embedding_chunks"]:
            sim = cosine_similarity(query_vector, chunk["vector"])
            scored_chunks.append({
                "text": chunk["text"],
                "score": sim,
                "source_file": entry["filename"],
                "title": entry.get("title", ""),
                "tags": entry.get("tags", []),
                "notes": entry.get("notes", ""),
                "filetype": entry.get("filetype", ""),
                "date_uploaded": entry.get("date_uploaded", ""),
                "category": entry.get("category", ""),
                "text_preview": entry.get("text_preview", "")
            })

    # Step 3: Sort by similarity
    top_chunks = sorted(scored_chunks, key=lambda x: x["score"], reverse=True)
    return top_chunks[:top_k] or [max(scored_chunks, key=lambda x: x["score"])]

