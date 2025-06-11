import streamlit as st
import json
from datetime import datetime
from core.user_paths import get_memory_index_path
from ui.file_cards import render_file_card
from ui.styles import CSS_VARIABLES
from typing import List, Dict, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def render_my_files_tab(user_id: str):
    """Render the My Files tab with filtering and sorting options.
    
    Args:
        user_id: User identifier
    """
    st.subheader("🗂️ My Files")

    memory_index_path = get_memory_index_path(user_id)

    if not memory_index_path.exists():
        st.info("No files found. Upload files in the Memory Manager tab.")
        return

    # Load memory index with error handling
    try:
        with open(memory_index_path, "r") as f:
            try:
                memory = json.load(f)
            except json.JSONDecodeError:
                st.error("Corrupted memory index. Please contact support.")
                return
    except Exception as e:
        st.error(f"Error loading files: {str(e)}")
        return

    if not memory:
        st.info("No files found. Upload files in the Memory Manager tab.")
        return

    # Sidebar Filters
    with st.expander("🔍 Filters & Sorting", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Category filter
            categories = sorted(set(item.get("category", "") for item in memory))
            selected_category = st.selectbox("Filter by Category", ["All"] + categories)
            
            # File type filter
            filetypes = sorted(set(item.get("filetype", "").upper() for item in memory))
            selected_filetype = st.selectbox("Filter by File Type", ["All"] + filetypes)
        
        with col2:
            # Search by title or tags
            search_text = st.text_input("Search by Title or Tags")
            
            # Sort options
            sort_options = [
                "Newest First",
                "Oldest First",
                "Title (A-Z)",
                "Title (Z-A)",
                "File Size (Largest First)",
                "File Size (Smallest First)"
            ]
            sort_by = st.selectbox("Sort by", sort_options)

    # Apply filters
    filtered_memory = []
    for item in memory:
        # Apply category filter
        if selected_category != "All" and item.get("category", "") != selected_category:
            continue
            
        # Apply filetype filter
        if selected_filetype != "All" and item.get("filetype", "").upper() != selected_filetype:
            continue

        # Apply search filter
        if search_text:
            title = item.get("title", "").lower()
            tags = [t.lower() for t in item.get("tags", [])]
            notes = item.get("notes", "").lower()
            filename = item.get("filename", "").lower()
            
            search_terms = search_text.lower().split()
            if not any(term in title or term in notes or 
                      any(term in tag for tag in tags) or 
                      term in filename for term in search_terms):
                continue

        filtered_memory.append(item)

    # Apply sorting
    if sort_by == "Newest First":
        filtered_memory.sort(key=lambda x: x.get("date_uploaded", ""), reverse=True)
    elif sort_by == "Oldest First":
        filtered_memory.sort(key=lambda x: x.get("date_uploaded", ""))
    elif sort_by == "Title (A-Z)":
        filtered_memory.sort(key=lambda x: x.get("title", "").lower())
    elif sort_by == "Title (Z-A)":
        filtered_memory.sort(key=lambda x: x.get("title", "").lower(), reverse=True)
    elif sort_by == "File Size (Largest First)":
        filtered_memory.sort(key=lambda x: x.get("file_size", 0), reverse=True)
    elif sort_by == "File Size (Smallest First)":
        filtered_memory.sort(key=lambda x: x.get("file_size", 0))

    # Display results count
    st.write(f"Showing {len(filtered_memory)} of {len(memory)} files")
    
    if not filtered_memory:
        st.warning("No results found matching your filters.")
    else:
        # Display files in a grid layout
        cols = st.columns(3)
        for i, item in enumerate(filtered_memory):
            with cols[i % 3]:
                render_file_card(item, user_id)

