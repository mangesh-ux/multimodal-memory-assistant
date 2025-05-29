import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.memory_handler import save_uploaded_file
from core.retriever import retrieve_relevant_chunks
import openai
import os
from dotenv import load_dotenv
load_dotenv()


openai.api_key = os.getenv("OPENAI_API_KEY")


st.set_page_config(page_title="Multimodal Memory Assistant", layout="wide")
st.title("🧠 Multimodal Memory Assistant")

tabs = st.tabs(["📂 Memory", "💬 Ask"])

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
                    entry = save_uploaded_file(
                        uploaded_file,
                        title=title,
                        tags=tags,
                        category=category,
                        notes=notes
                    )
                    st.success(f"{uploaded_file.name} saved to memory ✅")

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

        top_chunks = retrieve_relevant_chunks(user_input, top_k=5)
        context = ""
        for c in top_chunks:
            tag_str = ", ".join(c.get("tags", [])) or "None"
            context += (
                f"[Title: {c.get('title', 'Untitled')} | "
                f"Category: {c.get('category', 'Uncategorized')} | "
                f"Date Uploaded: {c.get('date_uploaded', '')[:10]} | "
                f"Tags: {tag_str}]\n"
                f"Notes: {c.get('notes', 'No notes provided.')}\n"
                f"Source: {c.get('source_file', '')}\n\n"
                f"{c['text'].strip()}\n\n"
                f"{'-'*60}\n\n"
            )


        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful memory assistant. Use the context provided to answer as precisely as possible."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion:\n{user_input}"
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
            st.markdown(f"🤖 **Assistant:** {msg['content']}")

    # Clear chat
    if st.button("🔁 Reset Conversation"):
        st.session_state.chat_history = []
        st.rerun()
