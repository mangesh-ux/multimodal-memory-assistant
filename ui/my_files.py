import streamlit as st
import json
from pathlib import Path
from core.user_paths import get_memory_index_path

def render_my_files_tab(user_id: str):
    memory_index_path = get_memory_index_path(user_id)

    st.subheader("📁 My Files - MemoBrain")

    # --- Filters (functional now) ---
    with st.sidebar:
        st.header("🔍 Filter Files")
        search_query = st.text_input("Search by keyword").lower().strip()
        selected_type = st.selectbox("File Type", ["All", "pdf", "image", "txt", "note"])
        selected_category = st.selectbox("Category", ["All", "personal", "research", "meeting", "idea", "thought"])

    # --- Load memory index ---
    if memory_index_path.exists():
        with open(memory_index_path, "r") as f:
            memory = json.load(f)
    else:
        memory = []

    if not memory:
        st.info("No files or notes found. Upload or add memory to get started.")
        return

    # --- Apply filters ---
    def matches(entry):
        if search_query:
            combined_text = " ".join([
                entry.get("title", ""),
                entry.get("notes", ""),
                " ".join(entry.get("tags", [])),
                entry.get("text_preview", "")
            ]).lower()
            if search_query not in combined_text:
                return False

        if selected_type != "All":
            if selected_type == "note" and entry.get("filepath"):
                return False
            if selected_type != "note" and entry.get("filetype") != selected_type:
                return False

        if selected_category != "All" and entry.get("category", "") != selected_category:
            return False

        return True

    filtered_memory = [e for e in memory if matches(e)]

    st.subheader(f"📂 Showing {len(filtered_memory)} matching item(s)")

    for i, entry in enumerate(reversed(filtered_memory)):
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
                if entry["filetype"] in {"png", "jpg", "jpeg"} and entry["filepath"]:
                    st.image(entry["filepath"], caption="Image Preview", use_column_width=True)
                elif entry["filetype"] == "pdf":
                    st.markdown("🔍 PDF uploaded. Text extracted is shown below.")
                    st.code(entry.get("text_preview", ""), language="text")
                elif entry["filetype"] == "txt":
                    st.code(entry.get("text_preview", ""), language="text")
                else:
                    st.write("No text available.")

            # Download button
            if entry.get("filepath") and Path(entry["filepath"]).exists():
                with open(entry["filepath"], "rb") as f:
                    file_bytes = f.read()
                st.download_button(
                    label="📥 Download Original File",
                    data=file_bytes,
                    file_name=entry["filename"]
                )

            if st.button("Delete", key=f"delete_{i}"):
                memory.remove(entry)
                with open(memory_index_path, "w") as f:
                    json.dump(memory, f, indent=2)
                st.warning("File deleted. Please refresh.")
                st.stop()
