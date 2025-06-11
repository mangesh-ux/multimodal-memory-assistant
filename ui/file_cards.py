import streamlit as st
import base64
from datetime import datetime
import os
import json
import tempfile
import shutil
from ui.styles import CARD_BG, TEXT_COLOR, TAG_COLOR, PADDING, RADIUS, BORDER
from core.user_paths import get_memory_index_path
from typing import Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def render_file_card(entry: Dict[str, Any], user_id: str):
    """Render a file card with metadata and actions.
    
    Args:
        entry: File entry dictionary
        user_id: User identifier
    """
    with st.container(border=True):
        # Format date
        try:
            date_str = datetime.fromisoformat(entry['date_uploaded']).strftime('%b %d, %Y')
        except (ValueError, KeyError):
            date_str = "Unknown date"
            
        # Get file size
        file_size = entry.get('file_size', 0)
        file_size_str = format_file_size(file_size) if file_size else "Unknown size"
        
        # Render card header
        st.markdown(
            f"""<div style="font-weight: bold; font-size: 1.1rem; color: {TEXT_COLOR};">
                {entry.get('title', 'Untitled')}
            </div>""",
            unsafe_allow_html=True
        )
        
        # File metadata
        st.markdown(
            f"""<div style="color: #666; font-size: 0.9rem;">
                {entry['filetype'].upper()} • {file_size_str} • {date_str}
            </div>""",
            unsafe_allow_html=True
        )
        
        # Tags and category
        tags = entry.get('tags', [])
        if tags:
            st.markdown(
                f"""<div style="margin-top: 0.5rem;">
                    <strong>Tags:</strong> {', '.join(tags)}
                </div>""",
                unsafe_allow_html=True
            )
            
        st.markdown(
            f"""<div>
                <strong>Category:</strong> {entry.get('category', 'None')}
            </div>""",
            unsafe_allow_html=True
        )
        
        # Notes (if any)
        if entry.get('notes'):
            st.markdown(
                f"""<div>
                    <strong>Notes:</strong> {entry.get('notes', '—')}
                </div>""",
                unsafe_allow_html=True
            )

        # Action buttons in columns
        col1, col2, col3 = st.columns(3)
        
        # Preview button
        with col1:
            preview_type = entry.get('preview_type', 'none')
            if preview_type != 'none':
                # Add a unique identifier (index + timestamp) to prevent duplicate keys
                unique_key = f"preview_{entry['source_hash']}_{id(entry)}"
                if st.button("👁️ Preview", key=unique_key):
                    st.session_state[f"preview_{entry['source_hash']}_open"] = True
        
        # File download
        with col2:
            if entry.get('filepath') and os.path.exists(entry['filepath']):
                try:
                    with open(entry['filepath'], "rb") as f:
                        data = f.read()
                    b64 = base64.b64encode(data).decode()
                    href = f'<a href="data:file/{entry["filetype"]};base64,{b64}" download="{entry["filename"]}" style="text-decoration:none;">⬇️ Download</a>'
                    st.markdown(href, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"File missing: {str(e)}")

        # Delete button
        with col3:
            # Add a unique identifier to prevent duplicate keys
            delete_key = f"delete_{entry['source_hash']}_{id(entry)}"
            if st.button("🗑 Delete", key=delete_key):
                try:
                    # Load memory index
                    memory_path = get_memory_index_path(user_id)
                    if os.path.exists(memory_path):
                        with open(memory_path, "r") as f:
                            memory = json.load(f)
                            
                        # Filter out the entry to delete
                        memory = [m for m in memory if m["source_hash"] != entry["source_hash"]]
                        
                        # Write with atomic pattern
                        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
                            json.dump(memory, tmp_file, indent=2)
                            tmp_path = tmp_file.name
                        
                        shutil.move(tmp_path, memory_path)
                        
                        # Delete the actual file if it exists
                        if entry.get('filepath') and os.path.exists(entry['filepath']):
                            os.remove(entry['filepath'])
                            
                        st.success("File deleted successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error deleting file: {str(e)}")
        
        # Show preview if requested
        if f"preview_{entry['source_hash']}_open" in st.session_state and st.session_state[f"preview_{entry['source_hash']}_open"]:
            st.markdown("### File Preview")
            preview_type = entry.get('preview_type', 'none')
            
            if preview_type == 'image' and entry.get('filepath') and os.path.exists(entry['filepath']):
                with open(entry['filepath'], "rb") as f:
                    image_data = f.read()
                st.image(image_data, caption=entry.get('title', entry.get('filename', 'Image')))
            elif preview_type == 'text' and entry.get('text_preview'):
                st.text_area("Content", value=entry.get('text_preview', ''), height=200, disabled=True)
            else:
                st.info("Preview not available for this file type.")
                
            # Add a unique identifier to prevent duplicate keys
            close_key = f"close_preview_{entry['source_hash']}_{id(entry)}"
            if st.button("Close Preview", key=close_key):
                st.session_state[f"preview_{entry['source_hash']}_open"] = False
                st.rerun()