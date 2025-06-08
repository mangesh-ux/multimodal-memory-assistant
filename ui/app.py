import streamlit as st
from ui.my_files import render_my_files_tab
from core.memory_handler import save_uploaded_file
from core.retriever import retrieve_relevant_chunks
from core.embedder import embed_and_store
from core.context_formatter import format_context_with_metadata
from core.user_paths import get_memory_index_path
from ui.login import authenticate_user
import json
import os
import openai
import hashlib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Setup
st.set_page_config(page_title="MemoBrain", layout="wide")
st.sidebar.title("📁 MemoBrain Navigation")
page = st.sidebar.radio("Go to", ["My Files", "Memory", "Ask"])

# Require login
user_id = authenticate_user()
if not user_id:
    st.error("Please log in to access MemoBrain.")
    st.stop()

# My Files
if page == "My Files":
    st.title("🗂️ Your Files")
    render_my_files_tab(user_id)

# Memory Tab
elif page == "Memory":
    st.title("📂 Memory Manager")

    uploaded_files = st.file_uploader(
        "Upload one or more files (PDF, image, or text)",
        type=["pdf", "png", "jpg", "jpeg", "txt"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.write("### Enter details for each uploaded file")

        for uploaded_file in uploaded_files:
            with st.expander(f"📝 {uploaded_file.name}"):
                title = st.text_input(f"Title for {uploaded_file.name}", key=f"title_{uploaded_file.name}")
                tags_input = st.text_input(f"Tags (comma-separated)", key=f"tags_{uploaded_file.name}")
                tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
                category = st.selectbox(f"Category", ["", "research", "personal", "meeting", "notes"], key=f"category_{uploaded_file.name}")
                notes = st.text_area(f"Notes", key=f"notes_{uploaded_file.name}")

                if st.button(f"Save {uploaded_file.name}", key=f"save_{uploaded_file.name}"):
                    entry, summary = save_uploaded_file(
                        uploaded_file, title, tags, category, notes, user_id
                    )
                    st.success(f"{uploaded_file.name} saved to memory ✅")
                    if summary:
                        st.markdown("#### 🧠 Summary by MemoBrain")
                        st.markdown(f"""
                            <div style="background-color:#f0f2f6;padding:1rem;border-radius:8px;border:1px solid #ccc;">
                                {summary}
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("[No summary generated for short file.]")

    # Add a manual note
    st.subheader("🧠 Add a Memory Note")
    note_text = st.text_area("Write something you want MemoBrain to remember")
    note_title = st.text_input("Optional title")
    note_tags = st.text_input("Tags (comma-separated)")
    note_category = st.selectbox("Category", ["", "idea", "meeting", "personal", "thought"])
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
            "embedding_chunks": [{"text": c, "vector": v} for c, v in zip(chunks, vectors)],
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

        st.success("Saved to memory ✅")

# Ask Tab
elif page == "Ask":
    st.title("💬 Ask MemoBrain")
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
            "You speak clearly and conversationally. You only use memory provided in context. "
            "If memory chunks have date/title/notes, mention that. If unsure, say you don’t know."
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
