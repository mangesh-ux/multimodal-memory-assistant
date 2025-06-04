import os
import json
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv
from core.user_paths import get_faiss_index_path, get_metadata_path

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# INDEX_PATH = os.path.join("core", "memory_store", "index.faiss")
# METADATA_PATH = os.path.join("core", "memory_store", "metadata.json")

def embed_query(query: str) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[query]
    )
    return np.array(response.data[0].embedding, dtype=np.float32).reshape(1, -1)

def retrieve_relevant_chunks(query: str, user_id: str, top_k=5) -> list[dict]:
    index_path = get_faiss_index_path(user_id)
    metadata_path = get_metadata_path(user_id)
    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        return []

    # Load FAISS index
    index = faiss.read_index(str(index_path))

    # Embed query
    query_vec = embed_query(query)

    # Search
    distances, indices = index.search(query_vec, top_k)
    indices = indices.flatten()

    # Load metadata
    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    results = []
    for i, idx in enumerate(indices):
        str_idx = str(idx)
        if str_idx in metadata:
            result = metadata[str_idx]
            result["score"] = float(distances[0][i])
            results.append(result)

    print("Query:", query)
    print("Top Matches:")
    for r in results:
        print("-", r["title"], "| Score:", r.get("score"))

    return results
