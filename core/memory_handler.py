import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
import shutil
import tempfile
from typing import Tuple, Dict, List, Optional, Any, Union
import uuid
from enum import Enum

from core.preprocess import extract_text, chunk_text
from core.embedder import embed_and_store
from core.user_paths import (
    get_user_data_dir,
    get_memory_index_path
)
from dotenv import load_dotenv
from openai import OpenAI
import numpy as np

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class MemoryType(Enum):
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    NOTE = "note"
    TASK = "task"
    EVENT = "event"
    RELATIONSHIP = "relationship"

class MemoryImportance(Enum):
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1

# MEMORY_INDEX_PATH = Path("data/memory_index.json")
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def get_file_hash(file_bytes: bytes) -> str:
    """Generate a unique hash for file content.
    
    Args:
        file_bytes: Raw bytes of the file
        
    Returns:
        MD5 hash of the file content
    """
    return hashlib.md5(file_bytes).hexdigest()


def sanitize_vector(v: Union[np.ndarray, list]) -> list:
    """Convert numpy arrays to Python lists for JSON serialization.
    
    Args:
        v: Vector to sanitize, either numpy array or list
        
    Returns:
        Sanitized list suitable for JSON serialization
    """
    if isinstance(v, np.ndarray):
        return v.tolist()
    elif isinstance(v, list):
        return [float(x) if isinstance(x, (np.float32, np.float64)) else x for x in v]
    return v


def auto_summarize(text: str, filename: str) -> Optional[str]:
    """Generate an automatic summary of document content using GPT.
    
    Args:
        text: Document text to summarize
        filename: Name of the file for context
        
    Returns:
        Summary text or None if text is too short or summarization fails
    """
    # Skip short files
    if len(text.split()) < 200:
        return None

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
        # Log the error but don't crash
        print(f"Summarization error: {str(e)}")
        return None


def calculate_memory_importance(text: str, metadata: dict) -> MemoryImportance:
    """Calculate the importance score of a memory based on content and metadata.
    
    Args:
        text: Memory content
        metadata: Associated metadata
        
    Returns:
        MemoryImportance enum value
    """
    # Factors that increase importance
    importance_factors = {
        "has_deadline": 2,
        "has_priority_tag": 2,
        "is_reference": 1,
        "has_relationships": 1,
        "is_frequently_accessed": 1
    }
    
    score = 3  # Default medium importance
    
    # Check metadata for importance factors
    if metadata.get("deadline"):
        score += importance_factors["has_deadline"]
    if any(tag in ["priority", "important", "critical"] for tag in metadata.get("tags", [])):
        score += importance_factors["has_priority_tag"]
    if metadata.get("is_reference", False):
        score += importance_factors["is_reference"]
    if metadata.get("relationships"):
        score += importance_factors["has_relationships"]
    if metadata.get("access_count", 0) > 10:
        score += importance_factors["is_frequently_accessed"]
    
    # Map score to enum
    if score >= 5:
        return MemoryImportance.CRITICAL
    elif score == 4:
        return MemoryImportance.HIGH
    elif score == 3:
        return MemoryImportance.MEDIUM
    elif score == 2:
        return MemoryImportance.LOW
    return MemoryImportance.MINIMAL

def create_memory_relationship(source_id: str, target_id: str, relationship_type: str, 
                             description: str = "") -> dict:
    """Create a relationship between two memories.
    
    Args:
        source_id: ID of the source memory
        target_id: ID of the target memory
        relationship_type: Type of relationship (e.g., "references", "depends_on", "related_to")
        description: Optional description of the relationship
        
    Returns:
        Relationship metadata dictionary
    """
    return {
        "id": str(uuid.uuid4()),
        "source_id": source_id,
        "target_id": target_id,
        "type": relationship_type,
        "description": description,
        "created_at": datetime.now().isoformat()
    }

def save_uploaded_file(uploaded_file, title: str, tags: list, category: str, 
                      notes: str, user_id: str, extracted_text: str) -> Tuple[dict, Optional[str]]:
    """Process and save an uploaded file with enhanced metadata.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        title: User-provided title
        tags: List of tags
        category: File category
        notes: Additional notes
        user_id: User identifier
        extracted_text: Pre-extracted text content
        
    Returns:
        Tuple of (file entry dict, summary text or None)
    """
    # Generate unique memory ID
    memory_id = str(uuid.uuid4())
    
    # Read file bytes only once
    file_bytes = uploaded_file.read()
    file_hash = get_file_hash(file_bytes)

    # Prepare file path
    ext = Path(uploaded_file.name).suffix.lower().strip(".")
    filename = f"{file_hash}_{uploaded_file.name}"
    file_path = get_user_data_dir(user_id) / filename
    
    # Use atomic write with temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(file_bytes)
        tmp_path = tmp_file.name
    
    # Move the temp file to the final location (atomic operation)
    shutil.move(tmp_path, file_path)

    # Process text into chunks with enhanced metadata
    raw_chunks = chunk_text(extracted_text)
    chunks = [{
        "text": c,
        "title": title or "",
        "tags": tags or [],
        "category": category or "",
        "notes": notes or "",
        "filename": uploaded_file.name,
        "date_uploaded": datetime.now().isoformat(),
        "file_size": len(file_bytes),
        "memory_id": memory_id,
        "version": 1,
        "access_count": 0,
        "last_accessed": datetime.now().isoformat(),
        "relationships": [],
        "context": {
            "created_at": datetime.now().isoformat(),
            "created_by": user_id,
            "source": "file_upload",
            "location": str(file_path)
        }
    } for c in raw_chunks]

    # Generate embeddings
    chunk_vectors = embed_and_store(chunks, user_id)

    # Generate summary if possible
    summary = auto_summarize(extracted_text, uploaded_file.name)
    if summary:
        summary_chunks = [{
            "text": summary,
            "title": f"Summary of {title or uploaded_file.name}",
            "tags": tags + ["summary"],
            "category": category,
            "notes": "Auto-generated summary for this document.",
            "filename": uploaded_file.name,
            "date_uploaded": datetime.now().isoformat(),
            "file_size": len(file_bytes),
            "memory_id": f"{memory_id}_summary",
            "version": 1,
            "access_count": 0,
            "last_accessed": datetime.now().isoformat(),
            "relationships": [create_memory_relationship(f"{memory_id}_summary", memory_id, "summarizes")],
            "context": {
                "created_at": datetime.now().isoformat(),
                "created_by": user_id,
                "source": "auto_summary",
                "location": str(file_path)
            }
        }]
        embed_and_store(summary_chunks, user_id)

    # Calculate memory importance
    importance = calculate_memory_importance(extracted_text, {
        "tags": tags,
        "category": category,
        "notes": notes
    })

    # Create enhanced entry
    entry = {
        "id": memory_id,
        "filename": uploaded_file.name,
        "filetype": ext,
        "filepath": str(file_path),
        "text_preview": extracted_text[:500],
        "date_uploaded": datetime.now().isoformat(),
        "embedding_chunks": [
            {"text": chunk, "vector": sanitize_vector(vec)}
            for chunk, vec in zip(chunks, chunk_vectors)
        ],
        "source_hash": file_hash,
        "title": title or "",
        "tags": tags or [],
        "category": category or "",
        "notes": notes or "",
        "file_size": len(file_bytes),
        "preview_type": "text" if ext in ["txt", "pdf"] else "image" if ext in ["png", "jpg", "jpeg"] else "none",
        "importance": importance.value,
        "version": 1,
        "access_count": 0,
        "last_accessed": datetime.now().isoformat(),
        "relationships": [],
        "context": {
            "created_at": datetime.now().isoformat(),
            "created_by": user_id,
            "source": "file_upload",
            "location": str(file_path)
        },
        "temporal_metadata": {
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "access_count": 0
        }
    }

    # Save with atomic write pattern
    memory_path = get_memory_index_path(user_id)
    try:
        if memory_path.exists():
            with open(memory_path, "r") as f:
                try:
                    index = json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: Corrupted memory index for user {user_id}. Creating new index.")
                    index = []
        else:
            index = []
    except Exception as e:
        print(f"Error loading memory index: {str(e)}")
        index = []

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
        json.dump(index + [entry], tmp_file, indent=2)
        tmp_path = tmp_file.name
    
    # Atomic replace
    shutil.move(tmp_path, memory_path)

    return entry, summary

def update_memory_access(memory_id: str, user_id: str) -> None:
    """Update access statistics for a memory.
    
    Args:
        memory_id: ID of the memory to update
        user_id: User identifier
    """
    memory_path = get_memory_index_path(user_id)
    if not memory_path.exists():
        return

    with open(memory_path, "r") as f:
        index = json.load(f)

    for entry in index:
        if entry["id"] == memory_id:
            entry["access_count"] += 1
            entry["last_accessed"] = datetime.now().isoformat()
            entry["temporal_metadata"]["last_accessed"] = datetime.now().isoformat()
            entry["temporal_metadata"]["access_count"] += 1
            break

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
        json.dump(index, tmp_file, indent=2)
        tmp_path = tmp_file.name
    
    shutil.move(tmp_path, memory_path)

def add_memory_relationship(source_id: str, target_id: str, relationship_type: str, 
                          description: str, user_id: str) -> None:
    """Add a relationship between two memories.
    
    Args:
        source_id: ID of the source memory
        target_id: ID of the target memory
        relationship_type: Type of relationship
        description: Description of the relationship
        user_id: User identifier
    """
    memory_path = get_memory_index_path(user_id)
    if not memory_path.exists():
        return

    with open(memory_path, "r") as f:
        index = json.load(f)

    relationship = create_memory_relationship(source_id, target_id, relationship_type, description)
    
    for entry in index:
        if entry["id"] == source_id:
            entry["relationships"].append(relationship)
            break

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
        json.dump(index, tmp_file, indent=2)
        tmp_path = tmp_file.name
    
    shutil.move(tmp_path, memory_path)
