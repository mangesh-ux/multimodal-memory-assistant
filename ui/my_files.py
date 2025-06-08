import streamlit as st
import json
from core.user_paths import get_memory_index_path
from ui.file_cards import render_file_card
from ui.styles import CSS_VARIABLES

def render_my_files_tab(user_id: str):
    st.subheader("🗂️ My Files")

    memory_index_path = get_memory_index_path(user_id)

    if not memory_index_path.exists():
        st.info("No files found.")
        return

    with open(memory_index_path, "r") as f:
        try:
            memory = json.load(f)
        except json.JSONDecodeError:
            st.error("Corrupted memory index.")
            return

    # Sidebar Filters (inside expander for cleanliness)
    with st.expander("🔍 Filters", expanded=True):
        categories = sorted(set(item.get("category", "") for item in memory))
        selected_category = st.selectbox("Filter by Category", ["All"] + categories)

        search_text = st.text_input("Search by Title or Tags")

    # Apply filters
    filtered_memory = []
    for item in memory:
        title = item.get("title", "").lower()
        tags = [t.lower() for t in item.get("tags", [])]
        category = item.get("category", "")

        if selected_category != "All" and category != selected_category:
            continue

        if search_text:
            if search_text.lower() not in title and all(search_text.lower() not in tag for tag in tags):
                continue

        filtered_memory.append(item)

    if not filtered_memory:
        st.warning("No results found.")
    else:
        for item in filtered_memory:
            render_file_card(item, user_id)

