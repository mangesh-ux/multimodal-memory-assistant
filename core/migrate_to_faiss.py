import faiss
import numpy as np
import json
from pathlib import Path

index_path = Path("core/memory_store/index.faiss")
metadata_path = Path("core/memory_store/metadata.json")
memory_json_path = Path("data/memory_index.json")

index_path.parent.mkdir(parents=True, exist_ok=True)

with open(memory_json_path, "r", encoding="utf-8") as f:
    old_memory = json.load(f)

vectors, metadatas = [], []

for entry in old_memory:
    for chunk in entry.get("embedding_chunks", []):
        vec = np.array(chunk["vector"], dtype=np.float32)
        vectors.append(vec)
        metadatas.append({
            "text": chunk["text"],
            "source_file": entry.get("filename", ""),
            "title": entry.get("title", ""),
            "tags": entry.get("tags", []),
            "notes": entry.get("notes", ""),
            "category": entry.get("category", ""),
            "date_uploaded": entry.get("date_uploaded", "")
        })

dim = len(vectors[0])
index = faiss.IndexFlatL2(dim)
index.add(np.array(vectors, dtype=np.float32))

faiss.write_index(index, str(index_path))

with open(metadata_path, "w", encoding="utf-8") as f:
    json.dump(metadatas, f, indent=2)

print("✅ FAISS index and metadata saved.")
