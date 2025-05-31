import os
import json
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INDEX_PATH = os.path.join("core", "memory_store", "index.faiss")
METADATA_PATH = os.path.join("core", "memory_store", "metadata.json")

def embed_text(texts):
    if isinstance(texts, str):
        texts = [texts]
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [np.array(e.embedding, dtype=np.float32) for e in response.data]

def save_to_faiss(vectors, metadatas):
    if not os.path.exists(INDEX_PATH):
        index = faiss.IndexFlatL2(len(vectors[0]))
        index_id = 0
        metadata_store = {}
    else:
        index = faiss.read_index(INDEX_PATH)
        try:
            with open(METADATA_PATH, "r") as f:
                metadata_store = json.load(f)
        except Exception:
            metadata_store = {}

        index_id = max(map(int, metadata_store.keys())) + 1

    # Add vectors to FAISS
    index.add(np.array(vectors).astype("float32")) # Add .astype("float32") when adding vectors (for strict FAISS compatibility)
    faiss.write_index(index, INDEX_PATH)

    # Add metadata
    for i, meta in enumerate(metadatas):
        metadata_store[str(index_id + i)] = meta

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata_store, f, indent=2)

def embed_and_store(chunks: list[dict]):
    if isinstance(chunks[0], str):
        # convert to dicts
        chunks = [{"text": t} for t in chunks]

    texts = [c["text"] for c in chunks]
    vectors = embed_text(texts)
    save_to_faiss(vectors, chunks)
    return vectors


def embed_text_list(text_list):  # Legacy support
    return embed_text(text_list)

