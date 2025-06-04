import os
import shutil
from pathlib import Path

def delete_user_memory(user_id: str):
    base_path = Path("data") / "users" / user_id

    if not base_path.exists():
        print(f"User '{user_id}' not found.")
        return

    # Delete FAISS index, metadata, and memory index.json
    index_path = base_path / "index.faiss"
    metadata_path = base_path / "metadata.json"
    memory_index_path = base_path / "memory_index.json"

    for path in [index_path, metadata_path, memory_index_path]:
        if path.exists():
            path.unlink()
            print(f"✅ Deleted: {path}")
        else:
            print(f"⚠️ Not found: {path}")

    # Optionally remove the user directory if it's empty
    try:
        base_path.rmdir()
        print(f"🧹 Removed empty directory: {base_path}")
    except OSError:
        print(f"📁 Directory not empty: {base_path}")

# Example usage:
delete_user_memory("mango")
