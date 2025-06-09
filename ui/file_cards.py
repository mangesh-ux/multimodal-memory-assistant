import streamlit as st
import base64
from datetime import datetime
from ui.styles import CARD_BG, TEXT_COLOR, TAG_COLOR, PADDING, RADIUS, BORDER
from core.user_paths import get_memory_index_path

def render_file_card(entry, user_id):
    with st.container(border=False):
        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; padding: {PADDING}; border-radius: {RADIUS}; border: {BORDER}; margin-bottom: 1rem;">
                <div style="font-weight: bold; font-size: 1.1rem; color: {TEXT_COLOR};">{entry.get('title', 'Untitled')}</div>
                <div style="color: #666; font-size: 0.9rem;">{entry['filetype'].upper()} • Uploaded {datetime.fromisoformat(entry['date_uploaded']).strftime('%b %d, %Y')}</div>
                <div style="margin-top: 0.5rem;"><strong>Tags:</strong> {', '.join(entry.get('tags', [])) or 'None'}</div>
                <div><strong>Category:</strong> {entry.get('category', 'None')}</div>
                <div><strong>Notes:</strong> {entry.get('notes', '—')}</div>
        """,
            unsafe_allow_html=True
        )

        # File download
        if entry['filepath']:
            try:
                with open(entry['filepath'], "rb") as f:
                    data = f.read()
                b64 = base64.b64encode(data).decode()
                href = f'<a href="data:file/{entry["filetype"]};base64,{b64}" download="{entry["filename"]}" style="text-decoration:none;">⬇️ Download</a>'
                st.markdown(href, unsafe_allow_html=True)
            except Exception as e:
                st.error("File missing")

        # Delete button
        if st.button("🗑 Delete", key=f"delete_{entry['source_hash']}"):
            import json, os

            memory_path = get_memory_index_path(user_id)
            if os.path.exists(memory_path):
                with open(memory_path, "r") as f:
                    memory = json.load(f)
                memory = [m for m in memory if m["source_hash"] != entry["source_hash"]]
                with open(memory_path, "w") as f:
                    json.dump(memory, f, indent=2)
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)