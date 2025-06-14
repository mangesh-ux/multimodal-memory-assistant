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
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import uuid

from ui.my_files import render_my_files_tab
from ui.timeline import render_timeline_view
from ui.relationships import render_relationships_view
from core.memory_handler import (
    save_uploaded_file, 
    update_memory_access,
    add_memory_relationship,
    MemoryType,
    MemoryImportance
)
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
    page_title="MemoBrain OS", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for modern OS-like interface
st.markdown("""
<style>
    /* Modern OS-like interface */
    .main {
        background-color: var(--background-color);
    }
    
    /* Dashboard cards */
    .dashboard-card {
        background-color: var(--background-color);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        transition: transform 0.2s;
        border: 1px solid var(--border-color);
    }
    
    .dashboard-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Memory importance indicators */
    .importance-critical { color: #dc3545; }
    .importance-high { color: #fd7e14; }
    .importance-medium { color: #ffc107; }
    .importance-low { color: #20c997; }
    .importance-minimal { color: #6c757d; }
    
    /* Memory type icons */
    .memory-type {
        font-size: 1.2rem;
        margin-right: 8px;
    }
    
    /* Relationship graph */
    .relationship-graph {
        background-color: var(--background-color);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid var(--border-color);
    }
    
    /* Timeline view */
    .timeline-item {
        border-left: 3px solid #007bff;
        padding-left: 15px;
        margin-bottom: 15px;
    }
    
    /* Mobile-friendly adjustments */
    @media (max-width: 768px) {
        .stButton button {width: 100%;}
        .stTextInput input {width: 100%;}
        .stSelectbox select {width: 100%;}
    }

    /* Dark mode variables */
    [data-theme="dark"] {
        --background-color: #262730;
        --border-color: #3e3e3e;
    }

    /* Light mode variables */
    [data-theme="light"] {
        --background-color: #ffffff;
        --border-color: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

def render_dashboard(user_id: str):
    """Render the main dashboard with memory statistics and insights."""
    st.title("🧠 MemoBrain OS Dashboard")
    
    # Load memory data
    memory_path = get_memory_index_path(user_id)
    if not memory_path.exists():
        st.info("No memories found. Start by uploading some files or creating notes!")
        return
        
    with open(memory_path, "r") as f:
        memories = json.load(f)
    
    # Calculate statistics
    total_memories = len(memories)
    total_size = sum(m.get("file_size", 0) for m in memories)
    categories = Counter(m.get("category", "uncategorized") for m in memories)
    importance_levels = Counter(m.get("importance", 3) for m in memories)
    
    # Create dashboard layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="dashboard-card">
                <h3>📊 Memory Statistics</h3>
                <p>Total Memories: {}</p>
                <p>Total Size: {:.1f} MB</p>
                <p>Categories: {}</p>
            </div>
        """.format(
            total_memories,
            total_size / (1024 * 1024),
            len(categories)
        ), unsafe_allow_html=True)
    
    with col2:
        # Create importance distribution pie chart
        fig = px.pie(
            values=list(importance_levels.values()),
            names=[f"Level {k}" for k in importance_levels.keys()],
            title="Memory Importance Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        # Create category distribution bar chart
        fig = px.bar(
            x=list(categories.keys()),
            y=list(categories.values()),
            title="Memory Categories"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent memories timeline
    st.markdown("### 📅 Recent Memories")
    recent_memories = sorted(
        memories,
        key=lambda x: x.get("temporal_metadata", {}).get("last_accessed", ""),
        reverse=True
    )[:5]
    
    for memory in recent_memories:
        with st.expander(f"{memory.get('title', 'Untitled')} ({memory.get('category', 'uncategorized')})"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(memory.get("text_preview", "")[:200] + "...")
            with col2:
                st.markdown(f"""
                    <div class="timeline-item">
                        <p>Last accessed: {memory.get('temporal_metadata', {}).get('last_accessed', 'Never')}</p>
                        <p>Access count: {memory.get('access_count', 0)}</p>
                        <p>Importance: {memory.get('importance', 3)}</p>
                    </div>
                """, unsafe_allow_html=True)
    
    # Memory relationships graph
    st.markdown("### 🔄 Memory Relationships")
    if any(m.get("relationships") for m in memories):
        # Create a simple network graph of relationships
        nodes = []
        edges = []
        for memory in memories:
            if memory.get("relationships"):
                nodes.append(memory["id"])
                for rel in memory["relationships"]:
                    edges.append((memory["id"], rel["target_id"]))
        
        fig = go.Figure(data=[
            go.Scatter(
                x=[i for i in range(len(nodes))],
                y=[0] * len(nodes),
                mode='markers+text',
                text=nodes,
                textposition="top center",
                marker=dict(size=20)
            )
        ])
        
        # Add edges
        for edge in edges:
            source_idx = nodes.index(edge[0])
            target_idx = nodes.index(edge[1])
            fig.add_shape(
                type="line",
                x0=source_idx, y0=0,
                x1=target_idx, y1=0,
                line=dict(color="gray", width=2)
            )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No memory relationships found. Create relationships between memories to see them here!")

# Page title
st.title("MemoBrain OS")

# User authentication
user_id = get_logged_in_user()
if not user_id:
    login_screen()
    st.stop()

# Render sidebar navigation
render_sidebar(user_id)

# Get current page from session state
page = st.session_state.get("current_page", "📊 Dashboard")

# Clear any previous page state
if "previous_page" not in st.session_state:
    st.session_state["previous_page"] = page
elif st.session_state["previous_page"] != page:
    # Clear any page-specific state when changing pages
    for key in list(st.session_state.keys()):
        if key.startswith("page_"):
            del st.session_state[key]
    st.session_state["previous_page"] = page

# Dashboard Tab
if page == "📊 Dashboard":
    render_dashboard(user_id)

# My Files Tab
elif page == "📂 My Files":
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
                                    <div style="
                                        background-color: rgba(49, 51, 63, 0.1); 
                                        border-left: 4px solid #FF4B4B; 
                                        padding: 1rem 1.5rem; 
                                        border-radius: 0.5rem; 
                                        margin: 1rem 0; 
                                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                                        font-size: 0.95rem;
                                        line-height: 1.5;
                                    ">
                                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                                            <span style="font-size: 1.2rem; margin-right: 0.5rem;">🤖</span>
                                            <strong>AI-Generated Summary</strong>
                                        </div>
                                        <div style="margin-left: 1.7rem;">{summary}</div>
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
                        "id": str(uuid.uuid4()),
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
                        "file_size": len(note_text.encode()),
                        "importance": 3,  # Default medium importance
                        "version": 1,
                        "access_count": 0,
                        "last_accessed": datetime.now().isoformat(),
                        "relationships": [],
                        "context": {
                            "created_at": datetime.now().isoformat(),
                            "created_by": user_id,
                            "source": "manual_note",
                            "location": ""
                        },
                        "temporal_metadata": {
                            "created_at": datetime.now().isoformat(),
                            "modified_at": datetime.now().isoformat(),
                            "last_accessed": datetime.now().isoformat(),
                            "access_count": 0
                        }
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
                    st.success("Note saved to memory ✅")
                except Exception as e:
                    st.error(f"Error saving note: {str(e)}")
        elif submit_button:
            st.warning("Please enter some content for your note.")

# Timeline Tab
elif page == "📅 Timeline":
    render_timeline_view(user_id)

# Relationships Tab
elif page == "🔄 Relationships":
    render_relationships_view(user_id)

# Search Tab
elif page == "🔍 Search":
    st.title("🔍 Memory Search")
    
    # Search interface
    search_query = st.text_input("Search your memories", placeholder="Enter your search query...")
    
    if search_query:
        with st.spinner("Searching memories..."):
            # Load memories
            memory_path = get_memory_index_path(user_id)
            if memory_path.exists():
                with open(memory_path, "r") as f:
                    memories = json.load(f)
                
                # Search through memories
                results = []
                for memory in memories:
                    # Check if query matches any metadata
                    if (search_query.lower() in memory.get("title", "").lower() or
                        search_query.lower() in memory.get("text_preview", "").lower() or
                        any(search_query.lower() in tag.lower() for tag in memory.get("tags", [])) or
                        search_query.lower() in memory.get("category", "").lower() or
                        search_query.lower() in memory.get("notes", "").lower()):
                        results.append(memory)
                
                if results:
                    st.markdown(f"### Found {len(results)} results")
                    
                    # Display results
                    for memory in results:
                        with st.expander(f"{memory.get('title', 'Untitled')} ({memory.get('category', 'uncategorized')})"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                # Memory content
                                st.markdown(memory.get("text_preview", "")[:500] + "...")
                                
                                # Tags
                                if memory.get("tags"):
                                    st.markdown(
                                        " ".join(f"`{tag}`" for tag in memory.get("tags", [])),
                                        unsafe_allow_html=True
                                    )
                                
                                # Notes
                                if memory.get("notes"):
                                    st.markdown("**Notes:**")
                                    st.markdown(memory.get("notes"))
                            
                            with col2:
                                # Metadata
                                st.markdown(f"""
                                    <div style="
                                        border-left: 3px solid #007bff;
                                        padding-left: 10px;
                                        margin: 10px 0;
                                    ">
                                        <p><strong>Created:</strong> {datetime.fromisoformat(memory.get('temporal_metadata', {}).get('created_at', '2000-01-01')).strftime('%Y-%m-%d %H:%M')}</p>
                                        <p><strong>Last accessed:</strong> {datetime.fromisoformat(memory.get('temporal_metadata', {}).get('last_accessed', '2000-01-01')).strftime('%Y-%m-%d %H:%M')}</p>
                                        <p><strong>Importance:</strong> {MemoryImportance(memory.get('importance', 3)).name}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                # Actions
                                if st.button("View Details", key=f"view_{memory.get('id', '')}"):
                                    update_memory_access(memory["id"], user_id)
                                    st.session_state["selected_memory"] = memory
                                    st.session_state["current_page"] = "📦 Memory Manager"
                                
                                if st.button("View Relationships", key=f"rel_{memory.get('id', '')}"):
                                    st.session_state["selected_memory"] = memory
                                    st.session_state["current_page"] = "🔄 Relationships"
                else:
                    st.info("No memories found matching your search query.")
            else:
                st.info("No memories found. Start by creating some memories!")

# Ask MemoBrain Tab
elif page == "🤖 Ask MemoBrain":
    st.title("🤖 Ask MemoBrain")
    st.markdown("Ask questions about your memories and get AI-powered insights.")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask MemoBrain anything..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Retrieve relevant chunks using semantic search
                    relevant_chunks = retrieve_relevant_chunks(prompt, user_id, top_k=5)
                    
                    if relevant_chunks:
                        # Format context with metadata
                        memory_context = format_context_with_metadata(relevant_chunks)
                        
                        # Prepare GPT-4 prompt
                        system_prompt = """You are MemoBrain, a helpful AI assistant that answers questions based on the user's personal memories.
                        Your responses should be:
                        1. Calm and professional
                        2. Based on the provided memory context
                        3. Include specific dates and temporal references
                        4. Acknowledge uncertainty when appropriate
                        5. Well-structured and easy to read
                        6. Include relevant metadata (categories, tags) when helpful
                        
                        If the memory context doesn't contain enough information to answer the question:
                        1. Acknowledge what you know from the context
                        2. Explain what information is missing
                        3. Suggest what additional memories might help
                        
                        Current question: {prompt}
                        
                        Memory context:
                        {memory_context}"""
                        
                        # Get GPT-4 response
                        response = openai.ChatCompletion.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": system_prompt.format(
                                    prompt=prompt,
                                    memory_context=memory_context
                                )},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=1000
                        )
                        
                        # Extract and format response
                        ai_response = response.choices[0].message.content
                        
                        # Add memory access tracking
                        for chunk in relevant_chunks:
                            if "id" in chunk:
                                update_memory_access(chunk["id"], user_id)
                    else:
                        ai_response = "I couldn't find any memories directly related to your question. Would you like me to search more broadly or help you create a new memory?"
                    
                    # Add AI response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                    st.markdown(ai_response)
                except Exception as e:
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    st.session_state.chat_history.append({"role": "assistant", "content": error_message})
                    st.markdown(error_message)
