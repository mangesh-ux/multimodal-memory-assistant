import streamlit as st
import json
from core.user_paths import get_memory_index_path
from ui.file_cards import render_file_card
from ui.styles import CSS_VARIABLES

def render_my_files_tab(user_id):
    st.subheader("🗂️ My Files")
    st.markdown(CSS_VARIABLES, unsafe_allow_html=True)

    memory_path = get_memory_index_path(user_id)
    if not memory_path.exists():
        st.info("No files found.")
        return

    with open(memory_path, "r") as f:
        try:
            memory = json.load(f)
        except json.JSONDecodeError:
            st.error("Memory index is corrupted.")
            return

    if not memory:
        st.info("No memory entries yet.")
        return

    # Display each file as a card
    for entry in reversed(memory):
        render_file_card(entry, user_id)
