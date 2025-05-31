import os

paths = [
    "core/memory_store/index.faiss",
    "core/memory_store/metadata.json",
    "data/memory_index.json"
]

for path in paths:
    if os.path.exists(path):
        os.remove(path)
        print(f"Deleted: {path}")
    else:
        print(f"Not found: {path}")
