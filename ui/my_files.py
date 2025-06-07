import streamlit as st
import json
from pathlib import Path
from core.user_paths import get_memory_index_path

def render_my_files_tab(user_id: str):
    memory_index_path = get_memory_index_path(user_id)

    st.subheader("📁 My Files - MemoBrain")

    # --- Filters (not functional yet) ---
    with st.sidebar:
        st.header("🔍 Filter Files")
        search_query = st.text_input("Search by keyword")
        selected_type = st.selectbox("File Type", ["All", "PDF", "Image", "Text", "Note"])
        selected_category = st.selectbox("Category", ["All", "Personal", "Research", "Meeting", "Idea", "Thought"])
        # date filter can be added later

    # --- Load memory index ---
    if memory_index_path.exists():
        with open(memory_index_path, "r") as f:
            memory = json.load(f)
    else:
        memory = []

    if not memory:
        st.info("No files or notes found. Upload or add memory to get started.")
        return

    st.subheader(f"📂 Showing {len(memory)} memory item(s)")

    for i, entry in enumerate(reversed(memory)):
        with st.expander(f"{entry.get('title') or entry['filename']}  •  {entry['filetype'].upper()}  •  Uploaded {entry['date_uploaded'][:10]}"):
            st.markdown(f"**Tags:** {', '.join(entry.get('tags', []))}  |  **Category:** {entry.get('category', '-')}")
            st.markdown(f"**Notes:** {entry.get('notes', '-')}")

            if st.button("Show Summary", key=f"summary_{i}"):
                summary_chunks = [c for c in entry["embedding_chunks"] if "summary" in c.get("title", "").lower()]
                if summary_chunks:
                    st.success(summary_chunks[0]['text'])
                else:
                    st.info("No summary found for this file.")

            if st.button("View Full Text", key=f"text_{i}"):
                st.code(entry.get("text_preview", "No preview available."), language="text")

            if st.button("Delete", key=f"delete_{i}"):
                memory.remove(entry)
                with open(memory_index_path, "w") as f:
                    json.dump(memory, f, indent=2)
                st.warning("File deleted. Please refresh.")
                st.stop()
