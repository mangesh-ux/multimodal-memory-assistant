# 🧠 MemoBrain – AI-Powered Smart File Manager

MemoBrain is an AI-native file management system built with Streamlit, OpenAI, and FAISS. Unlike traditional storage tools, MemoBrain automatically reads, indexes, summarizes, and enables intelligent search and Q&A over all your files and notes.

## ✨ Key Features

- 📂 Upload and store PDFs, images, and notes with structured metadata
- 🧠 GPT-4o powered document summarization and metadata suggestion
- 🔍 Semantic search with FAISS vector store
- 💬 Ask questions about your memory using natural language
- 🗂️ Rich file previews with category, date, and metadata display
- 🔐 User authentication with individual memory isolation
- 🚀 Deployed and running on AWS EC2

## ⚙️ Tech Stack

- Python, Streamlit
- OpenAI GPT-4o (summarization + metadata inference)
- FAISS (vector storage)
- PyMuPDF + OCR (document parsing)
- Deployed on: AWS EC2 (Ubuntu)

## 📸 Screenshots

| Smart File Manager UI | Ask Anything Chat |
|------------------------|-------------------|
| ![Alt text](image-1.png) | ![Alt text](image-2.png) |
| ![Alt text](image-4.png) | ![Alt text](image-3.png) |

## 🚀 Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/memobrain.git
   cd memobrain
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your OpenAI API key in a `.env` file:
   ```env
   OPENAI_API_KEY=your-key-here
   ```

4. Run the app:
   ```bash
   streamlit run ui/app.py
   ```

## 🧪 Test Use Cases

Sign up as a new user and upload test files. Then try asking:

- “What did I upload last week?”
- “Summarize my meeting notes on insurance claims.”
- “Find the file related to X from March.”

## 🛠️ Future Enhancements

- RAG-based long document chat
- Email/file ingestion pipelines
- User analytics dashboard
- Tag-based auto-classification

## 🙌 Acknowledgements

Special thanks to OpenAI and the Streamlit community for enabling rapid prototyping and innovation.

---

Built with ❤️ by Mangesh Gupta