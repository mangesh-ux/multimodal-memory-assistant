from pathlib import Path

def get_user_base_path(user_id: str) -> Path:
    path = Path(f"data/users/{user_id}")
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_memory_index_path(user_id: str) -> Path:
    return get_user_base_path(user_id) / "memory_index.json"

def get_faiss_index_path(user_id: str) -> Path:
    return get_user_base_path(user_id) / "index.faiss"

def get_metadata_path(user_id: str) -> Path:
    return get_user_base_path(user_id) / "metadata.json"

def get_user_data_dir(user_id: str) -> Path:
    path = get_user_base_path(user_id) / "docs"
    path.mkdir(parents=True, exist_ok=True)
    return path
