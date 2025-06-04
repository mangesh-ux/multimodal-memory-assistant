import hashlib
import json
import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.memory_handler import save_uploaded_file
from core.retriever import retrieve_relevant_chunks
from core.embedder import embed_text, embed_and_store
import openai
import os
from datetime import datetime
from core.context_formatter import format_context_with_metadata
import streamlit.components.v1 as components
from core.user_paths import get_memory_index_path
from dotenv import load_dotenv
load_dotenv()


openai.api_key = os.getenv("OPENAI_API_KEY")


st.set_page_config(page_title="Multimodal Memory Assistant", layout="wide")
st.title("🧠 Multimodal Memory Assistant")

tabs = st.tabs(["📂 Memory", "💬 Ask"])

user_id = "demo_user"

# Memory Tab
with tabs[0]:
    st.subheader("📂 Memory Manager")

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
                tags_input = st.text_input(f"Tags (comma-separated) for {uploaded_file.name}", key=f"tags_{uploaded_file.name}")
                tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
                category = st.selectbox(f"Category for {uploaded_file.name}", ["", "research", "personal", "meeting", "notes"], key=f"category_{uploaded_file.name}")
                notes = st.text_area(f"Notes for {uploaded_file.name}", key=f"notes_{uploaded_file.name}")

                if st.button(f"Save {uploaded_file.name}", key=f"save_{uploaded_file.name}"):
                    entry, summary = save_uploaded_file(
                            uploaded_file,
                            title=title,
                            tags=tags,
                            category=category,
                            notes=notes,
                            user_id=user_id
                        )

                    st.success(f"{uploaded_file.name} saved to memory ✅")
                    if summary:
                        print("SUMMARY GENERATED:", summary)
                        with st.container():
                            st.markdown("### 🧠 Summary by Mongo")
                            st.markdown(
                                f"""
                                <div style="background-color: #f7f8fa; padding: 1rem 1.2rem; border-radius: 8px; border: 1px solid #ddd;">
                                {summary}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        components.html(f"""
                            <textarea id="mongo-summary" style="width: 100%; height: 0; opacity: 0;">{summary}</textarea>
                            <button onclick="navigator.clipboard.writeText(document.getElementById('mongo-summary').value)"
                                    style="margin-top: 0.5rem;">📋 Copy Summary</button>
                        """, height=40)

                    else:
                        st.info("[No summary generated for the short file.]")
    
    st.subheader("🧠 Add a Memory Note")

    note_text = st.text_area("Write something you want Mongo to remember")
    note_title = st.text_input("Optional title")
    note_tags = st.text_input("Tags (comma-separated)")
    note_category = st.selectbox("Category", ["", "idea", "meeting", "personal", "thought"])
    note_notes = st.text_input("Additional notes")

    if st.button("Save Note"):
        # Save as virtual file (text only)
        entry = {
            "filename": f"user_note_{datetime.now().isoformat()}.txt",
            "filetype": "txt",
            "filepath": "",  # No file
            "text_preview": note_text[:500],
            "date_uploaded": datetime.now().isoformat(),
            "embedding_chunks": [],
            "source_hash": hashlib.md5(note_text.encode()).hexdigest(),
            "title": note_title,
            "tags": [t.strip() for t in note_tags.split(",") if t],
            "category": note_category,
            "notes": note_notes
        }

        # Chunk + embed
        from core.preprocess import chunk_text

        chunks = chunk_text(note_text)
        vectors = embed_and_store(chunks, user_id)
        entry["embedding_chunks"] = [{"text": c, "vector": v} for c, v in zip(chunks, vectors)]

        # Append to memory_index.json
        memory_path = get_memory_index_path(user_id)
        if memory_path.exists():
            with open(memory_path, "r") as f:
                memory = json.load(f)
        else:
            memory = []

        memory.append(entry)

        with open(memory_path, "w") as f:
            json.dump(memory, f, indent=2)


        st.success("Saved to memory ✅")


# Ask Tab
with tabs[1]:
    st.subheader("💬 Ask Me Anything")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Input area
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Your message", placeholder="Ask a question about your memories...")
        submitted = st.form_submit_button("Send")

    if submitted and user_input:
        # Append user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        top_chunks = retrieve_relevant_chunks(user_input, user_id=user_id, top_k=5)
        context = format_context_with_metadata(top_chunks)

        if top_chunks:
            st.caption(f"🧠 Mongo is answering based on {len(top_chunks)} memory snippet(s) with top similarity: {top_chunks[0]['score']:.3f}")
        else:
            st.caption("🧠 Mongo couldn't find anything relevant in memory.")
        
        st.write("Debug — Top Chunks:", top_chunks)

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Mongo — a calm, helpful memory assistant. "
                        "You speak clearly and conversationally, like a natural assistant. "
                        "You are grounded — you only use information provided in the context. "
                        "If memory chunks are provided, always answer by referencing them. "
                        "If a memory chunk includes a date, title, or notes, clarify that you're recalling from that memory. "
                        "If you don't know something from context, confidently say you don't know. "
                        "Use markdown when it helps make the answer easier to read (e.g. for bullet points, headings, code, or bold emphasis)."
                    )
                }
,
                {
                    "role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{user_input}"
                }
            ]
        )


        assistant_reply = response.choices[0].message.content.strip()
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})


    # Display conversation
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"🧍‍♂️ **You:** {msg['content']}")
        else:
            st.markdown(f"🧠 Mongo** {msg['content']}")

    # Clear chat
    if st.button("🔁 Reset Conversation"):
        st.session_state.chat_history = []
        st.rerun()
