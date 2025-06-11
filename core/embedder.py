import os
import json
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv
from core.user_paths import get_faiss_index_path, get_metadata_path
import tempfile
import shutil
import logging
from typing import List, Dict, Any, Union, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def embed_text(texts: Union[str, List[str]]) -> List[np.ndarray]:
    """Generate embeddings for text using OpenAI's embedding model.
    
    Args:
        texts: Single text string or list of text strings
        
    Returns:
        List of embedding vectors as numpy arrays
    """
    if isinstance(texts, str):
        texts = [texts]
        
    # Handle empty input
    if not texts or all(not t.strip() for t in texts):
        logger.warning("Attempted to embed empty text")
        # Return zero vectors of appropriate dimension (1536 for text-embedding-3-small)
        return [np.zeros(1536, dtype=np.float32) for _ in range(len(texts))]
    
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [np.array(e.embedding, dtype=np.float32) for e in response.data]
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        # Return zero vectors as fallback
        return [np.zeros(1536, dtype=np.float32) for _ in range(len(texts))]

def save_to_faiss(vectors: List[np.ndarray], metadatas: List[Dict[str, Any]], user_id: str) -> bool:
    """Save vectors and metadata to FAISS index and JSON file.
    
    Args:
        vectors: List of embedding vectors
        metadatas: List of metadata dictionaries
        user_id: User identifier
        
    Returns:
        True if successful, False otherwise
    """
    index_path = get_faiss_index_path(user_id)
    metadata_path = get_metadata_path(user_id)
    
    try:
        # Load or create index
        if not os.path.exists(index_path):
            # Create new index with appropriate dimension
            index = faiss.IndexFlatL2(len(vectors[0]))
            index_id = 0
            metadata_store = {}
        else:
            # Load existing index
            index = faiss.read_index(str(index_path))
            try:
                with open(metadata_path, "r") as f:
                    metadata_store = json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata, creating new: {str(e)}")
                metadata_store = {}

            # Get next available ID
            index_id = max(map(int, metadata_store.keys() or ["0"])) + 1

        # Add vectors to FAISS with proper type conversion
        vectors_array = np.array(vectors).astype("float32")
        index.add(vectors_array)
        
        # Write index with atomic pattern
        temp_index_path = f"{index_path}.temp"
        faiss.write_index(index, temp_index_path)
        os.replace(temp_index_path, index_path)

        # Add metadata with atomic write
        for i, meta in enumerate(metadatas):
            metadata_store[str(index_id + i)] = meta

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            json.dump(metadata_store, tmp_file, indent=2)
            tmp_path = tmp_file.name
        
        shutil.move(tmp_path, metadata_path)
        return True
        
    except Exception as e:
        logger.error(f"Error saving to FAISS: {str(e)}")
        return False

def embed_and_store(chunks: Union[List[str], List[Dict[str, Any]]], user_id: str) -> List[np.ndarray]:
    """Embed text chunks and store in FAISS index.
    
    Args:
        chunks: List of text strings or dictionaries with 'text' key
        user_id: User identifier
        
    Returns:
        List of embedding vectors
    """
    # Convert string chunks to dictionaries if needed
    if isinstance(chunks[0], str):
        chunks = [{"text": t} for t in chunks]

    # Extract text for embedding
    texts = [c["text"] for c in chunks]
    
    # Generate embeddings
    vectors = embed_text(texts)
    
    # Save to FAISS
    save_to_faiss(vectors, chunks, user_id)
    
    return vectors


def embed_text_list(text_list: List[str]) -> List[np.ndarray]:  
    """Legacy support function for embedding text lists.
    
    Args:
        text_list: List of text strings to embed
        
    Returns:
        List of embedding vectors
    """
    return embed_text(text_list)

