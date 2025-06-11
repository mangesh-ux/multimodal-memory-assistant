from pathlib import Path
import streamlit as st
import json
import os
import openai
import hashlib
from datetime import datetime
from dotenv import load_dotenv
import sys
import logging
from typing import List, Dict, Any, Optional

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
from streamlit_option_menu import option_menu
from ui.sidebar import render_sidebar
from ui.file_preview import render_file_preview

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Application constants
DEFAULT_CATEGORIES = [
    "personal", "work", "finance", "health", "education",
    "legal", "creative", "research", "travel", "communication",
    "project", "other"
]

# Setup page configuration
st.set_page_config(
    page_title="MemoBrain", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for mobile responsiveness
st.markdown("""
<style>
    /* Mobile-friendly adjustments */
    @media (max-width: 768px) {
        .stButton button {width: 100%;}
        .stTextInput input {width: 100%;}
        .stSelectbox select {width: 100%;}
    }
    
    /* Improve file card display */
    .file-card {transition: transform 0.2s;}
    .file-card:hover {transform: translateY(-2px);}
</style>
""", unsafe_allow_html=True)

# Page title
st.title("MemoBrain File Manager")

# User authentication
user_id = get_logged_in_user()
if not user_id:
    login_screen()
    st.stop()

# Render sidebar navigation
render_sidebar(user_id)
page = st.session_state.get("current_page", "📦 Memory Manager")

# My Files Tab
if page == "📂 My Files":
    render_my_files_tab(user_id)

# Memory Manager Tab
elif page == "📦 Memory Manager":
    st.title("🧠 Memory Manager")
    st.markdown("Upload documents or write memory notes. Everything becomes searchable.")

    # File uploader
    uploaded_files = st.file_uploader(
        "Upload one or more files (PDF, image, or text)",
        type=["pdf", "png", "jpg", "jpeg", "txt"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.write("### Enter details for each uploaded file")

        for uploaded_file in uploaded_files:
            st.markdown(f"### 📄 File: {uploaded_file.name}")
            
            # Create a hash for the file
            file_bytes = uploaded_file.read()
            file_hash = hashlib.md5(file_bytes).hexdigest()
            ext = Path(uploaded_file.name).suffix.lower().strip(".")
            filename = f"{file_hash}_{uploaded_file.name}"

            # Save to temp file to extract text
            temp_path = Path("temp") / filename
            temp_path.parent.mkdir(exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(file_bytes)

            # Extract text with error handling
            try:
                extracted_text = extract_text(temp_path, ext)
                if not extracted_text.strip():
                    st.warning(f"⚠️ No text could be extracted from {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error extracting text: {str(e)}")
                extracted_text = f"[Error extracting text: {str(e)}]"

            # Generate metadata suggestions
            with st.spinner("Generating metadata suggestions..."):
                suggested = generate_metadata(extracted_text[:1000], uploaded_file.name)

            # File metadata form
            with st.expander(f"📝 {uploaded_file.name}", expanded=True):
                # Two-column layout for metadata
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    title = st.text_input("Title", value=suggested.get("title", ""), key=f"title_{filename}")
                    tags_input = st.text_input("Tags (comma-separated)", value=", ".join(suggested.get("tags", [])), key=f"tags_{filename}")
                    tags = [t.strip() for t in tags_input.split(",") if t.strip()]
                    category = st.selectbox(
                        "Category",
                        DEFAULT_CATEGORIES + ["[Other]"],
                        key=f"category_{uploaded_file.name}"
                    )
                    notes = st.text_area("Notes", value=suggested.get("notes", ""), key=f"notes_{filename}")
                
                with col2:
                    # Show file preview based on type
                    st.markdown("### Preview")
                    if ext in ["png", "jpg", "jpeg"]:
                        st.image(file_bytes, caption=uploaded_file.name, width=250)
                    elif ext == "txt":
                        st.text_area("Content Preview", value=extracted_text[:500] + "...", height=200, disabled=True)
                    elif ext == "pdf":
                        st.markdown(f"PDF file: {len(extracted_text.split())} words extracted")
                        st.text_area("Content Preview", value=extracted_text[:500] + "...", height=200, disabled=True)
                    
                    # Display file size
                    file_size_kb = len(file_bytes) / 1024
                    file_size_display = f"{file_size_kb:.1f} KB" if file_size_kb < 1024 else f"{file_size_kb/1024:.1f} MB"
                    st.info(f"File size: {file_size_display}")

                # Save button
                if st.button(f"Save {uploaded_file.name}", key=f"save_{uploaded_file.name}"):
                    with st.spinner("Processing file..."):
                        try:
                            entry, summary = save_uploaded_file(
                                uploaded_file, title, tags, category, notes, user_id, extracted_text
                            )
                            st.success(f"{uploaded_file.name} saved to memory ✅")
                            
                            # Show summary if available
                            if summary:
                                st.markdown("#### 🧠 Auto Summary")
                                st.markdown(f"""
                                    <div style="background-color:#f0f2f6;padding:1rem;border-radius:8px;border:1px solid #ccc;">
                                        {summary}
                                    </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.info("[No summary generated for this file.]")
                        except Exception as e:
                            st.error(f"Error saving file: {str(e)}")

    # Add a manual note section
    st.divider()
    st.subheader("Add a Manual Note")
    
    # Form for manual notes
    with st.form("manual_note_form"):
        note_text = st.text_area("Memory Content", height=200)
        col1, col2 = st.columns(2)
        
        with col1:
            note_title = st.text_input("Title")
            note_tags = st.text_input("Tags (comma-separated)")
        
        with col2:
            note_category = st.selectbox("Category", DEFAULT_CATEGORIES)
            note_notes = st.text_input("Additional notes")
        
        submit_button = st.form_submit_button("Save Note")
        
        if submit_button and note_text.strip():
            with st.spinner("Processing note..."):
                try:
                    from core.preprocess import chunk_text
                    chunks = chunk_text(note_text)
                    vectors = embed_and_store(chunks, user_id)

                    # Create note entry
                    entry = {
                        "filename": f"user_note_{datetime.now().isoformat()}.txt",
                        "filetype": "txt",
                        "filepath": "",
                        "text_preview": note_text[:500],
                        "date_uploaded": datetime.now().isoformat(),
                        "embedding_chunks": [
                            {"text": c, "vector": v.tolist() if hasattr(v, 'tolist') else v} 
                            for c, v in zip(chunks, vectors)
                        ],
                        "source_hash": hashlib.md5(note_text.encode()).hexdigest(),
                        "title": note_title,
                        "tags": [t.strip() for t in note_tags.split(",") if t],
                        "category": note_category,
                        "notes": note_notes,
                        "file_size": len(note_text.encode())
                    }

                    # Save to memory index
                    memory_path = get_memory_index_path(user_id)
                    try:
                        memory = json.load(open(memory_path)) if memory_path.exists() else []
                    except json.JSONDecodeError:
                        memory = []
                        
                    memory.append(entry)
                    
                    # Use atomic write pattern
                    import tempfile
                    import shutil
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
                        json.dump(memory, tmp_file, indent=2)
                        tmp_path = tmp_file.name
                    
                    shutil.move(tmp_path, memory_path)
                    
                    st.success("✅ Note saved to memory.")
                except Exception as e:
                    st.error(f"Error saving note: {str(e)}")
        elif submit_button:
            st.warning("Please enter some content for your note.")

# Ask MemoBrain Tab
elif page == "💬 Ask MemoBrain":
    st.title("💬 Ask MemoBrain")
    st.markdown("Ask any question. MemoBrain will answer based on your uploaded memory.")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    prompt = st.chat_input("Ask a question about your memories...")
    if prompt:
        # Add user message to chat
        st.chat_message("user").markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Retrieve relevant chunks
        with st.spinner("Searching your memories..."):
            try:
                top_chunks = retrieve_relevant_chunks(prompt, user_id=user_id, top_k=5)
                if not top_chunks:
                    st.warning("No relevant memories found. Try uploading more files or rephrasing your question.")
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": "I couldn't find any relevant information in your memories. Try uploading more files or rephrasing your question."
                    })
                    st.rerun()
                    
                context = format_context_with_metadata(top_chunks)

                # Generate response
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
            except Exception as e:
                error_message = f"Error processing your question: {str(e)}"
                st.error(error_message)
                st.session_state.chat_history.append({"role": "assistant", "content": error_message})

    # Reset conversation button
    if st.button("🔁 Reset Conversation"):
        st.session_state.chat_history = []
        st.rerun()
        st.rerun()
