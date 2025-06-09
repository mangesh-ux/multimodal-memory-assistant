from pathlib import Path
import streamlit as st
import json
import os
import openai
import hashlib
from datetime import datetime
from dotenv import load_dotenv
import sys

from ui.my_files import render_my_files_tab
from core.memory_handler import save_uploaded_file
from core.retriever import retrieve_relevant_chunks
from core.embedder import embed_and_store
from core.context_formatter import format_context_with_metadata
from core.user_paths import get_memory_index_path
from ui.login import login_screen, get_logged_in_user
import base64
from core.preprocess import extract_text
from core.metadata_suggester import generate_metadata

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Setup
st.set_page_config(page_title="MemoBrain", layout="wide")
st.title("MemoBrain File Manager")
DEFAULT_CATEGORIES = [
                    "personal", "work", "finance", "health", "education",
                    "legal", "creative", "research", "travel", "communication",
                    "project", "other"
                ]

# User authentication
user_id = get_logged_in_user()
if not user_id:
    login_screen()
    st.stop()

st.sidebar.title("📁 MemoBrain Navigation")
st.sidebar.success(f"👤 Logged in as: {user_id}")

page = st.sidebar.selectbox("Navigate", ["📁 My Files", "🧠 Memory Manager", "💬 Ask MemoBrain"])
# My Files
if page == "📁 My Files":
    # st.title("🗂️ Your Files")
    render_my_files_tab(user_id)

# Memory Tab
elif page == "🧠 Memory Manager":
    st.title("🧠 Memory Manager")
    st.markdown("Upload documents or write memory notes. Everything becomes searchable.")

    uploaded_files = st.file_uploader(
        "Upload one or more files (PDF, image, or text)",
        type=["pdf", "png", "jpg", "jpeg", "txt"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.write("### Enter details for each uploaded file")

        for uploaded_file in uploaded_files:
            st.markdown("### 📄 File Metadata")
            file_bytes = uploaded_file.read()
            file_hash = hashlib.md5(file_bytes).hexdigest()
            ext = Path(uploaded_file.name).suffix.lower().strip(".")
            filename = f"{file_hash}_{uploaded_file.name}"

            # Save to temp file to extract text
            temp_path = Path("temp") / filename
            temp_path.parent.mkdir(exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(file_bytes)

            try:
                extracted_text = extract_text(temp_path, ext)
            except Exception as e:
                extracted_text = f"[Error extracting text: {e}]"

            # Suggest metadata
            suggested = generate_metadata(extracted_text[:3000], uploaded_file.name)

            with st.expander(f"📝 {uploaded_file.name}"):
                title = st.text_input("Title", value=suggested.get("title", ""), key=f"title_{filename}")
                tags_input = st.text_input("Tags (comma-separated)", value=", ".join(suggested.get("tags", [])), key=f"tags_{filename}")
                tags = [t.strip() for t in tags_input.split(",") if t.strip()]
                category = st.selectbox(
                    f"Choose a category for {uploaded_file.name}",
                    DEFAULT_CATEGORIES + ["[Other]"],
                    key=f"category_{uploaded_file.name}"
                )
                notes = st.text_area("Notes", value=suggested.get("notes", ""), key=f"notes_{filename}")

                if st.button(f"Save {uploaded_file.name}", key=f"save_{uploaded_file.name}"):
                    entry, summary = save_uploaded_file(
                        uploaded_file, title, tags, category, notes, user_id
                    )
                    st.success(f"{uploaded_file.name} saved to memory ✅")
                    if summary:
                        st.markdown("#### 🧠 Auto Summary")
                        st.markdown(f"""
                            <div style="background-color:#8db0f7;padding:1rem;border-radius:8px;border:1px solid #ccc;">
                                {summary}
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("[No summary generated for short file.]")

    # Add a manual note
    st.divider()
    st.subheader("Add a Manual Note")
    note_text = st.text_area("Memory Content")
    note_title = st.text_input("Optional title")
    note_tags = st.text_input("Tags (comma-separated)")
    note_category = st.selectbox("Category", DEFAULT_CATEGORIES)
    note_notes = st.text_input("Additional notes")

    if st.button("Save Note"):
        from core.preprocess import chunk_text
        chunks = chunk_text(note_text)
        vectors = embed_and_store(chunks, user_id)

        entry = {
            "filename": f"user_note_{datetime.now().isoformat()}.txt",
            "filetype": "txt",
            "filepath": "",
            "text_preview": note_text[:500],
            "date_uploaded": datetime.now().isoformat(),
            "embedding_chunks": [{"text": c, "vector": v.tolist() if hasattr(v, 'tolist') else v} for c, v in zip(chunks, vectors)],
            "source_hash": hashlib.md5(note_text.encode()).hexdigest(),
            "title": note_title,
            "tags": [t.strip() for t in note_tags.split(",") if t],
            "category": note_category,
            "notes": note_notes
        }

        memory_path = get_memory_index_path(user_id)
        memory = json.load(open(memory_path)) if memory_path.exists() else []
        memory.append(entry)
        json.dump(memory, open(memory_path, "w"), indent=2)

        st.success("✅ Note saved to memory.")

# Ask Tab
elif page == "💬 Ask MemoBrain":
    st.title("💬 Ask MemoBrain")
    st.markdown("Ask any question. MemoBrain will answer based on your uploaded memory.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask a question about your memories...")
    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        top_chunks = retrieve_relevant_chunks(prompt, user_id=user_id, top_k=5)
        context = format_context_with_metadata(top_chunks)

        system_prompt = (
            "You are MemoBrain — a calm, helpful memory assistant. "
            "You should summarize clearly, reference file titles and dates when available, and admit when unsure."
        )

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{prompt}"}
            ]
        )

        reply = response.choices[0].message.content.strip()
        st.chat_message("assistant").markdown(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    if st.button("🔁 Reset Conversation"):
        st.session_state.chat_history = []
        st.rerun()
