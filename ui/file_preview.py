import streamlit as st
import os
from PIL import Image
import io
from pathlib import Path
import logging
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def render_file_preview(file_path: str, file_type: str, title: Optional[str] = None):
    """Render a preview of a file based on its type.
    
    Args:
        file_path: Path to the file
        file_type: Type of file (pdf, txt, png, jpg, etc.)
        title: Optional title to display
    """
    if not os.path.exists(file_path):
        st.error("File not found.")
        return
        
    file_type = file_type.lower()
    
    # Display title if provided
    if title:
        st.markdown(f"### {title}")
    
    try:
        # Image preview
        if file_type in ["png", "jpg", "jpeg"]:
            image = Image.open(file_path)
            st.image(image, caption=Path(file_path).name)
            
            # Display image metadata
            st.markdown("#### Image Information")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Format: {image.format}")
                st.write(f"Mode: {image.mode}")
            with col2:
                st.write(f"Size: {image.width} x {image.height} pixels")
                file_size = os.path.getsize(file_path)
                st.write(f"File size: {file_size / 1024:.1f} KB")
        
        # Text file preview
        elif file_type == "txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            st.text_area("File Content", value=content, height=400)
            
            # Display text statistics
            word_count = len(content.split())
            line_count = len(content.splitlines())
            st.write(f"Word count: {word_count}, Line count: {line_count}")
        
        # PDF preview
        elif file_type == "pdf":
            # Display PDF info
            file_size = os.path.getsize(file_path)
            st.write(f"PDF file size: {file_size / 1024:.1f} KB")
            
            # Extract text preview
            from core.preprocess import extract_pdf_text
            text_preview = extract_pdf_text(Path(file_path))[:1000] + "..."
            st.text_area("PDF Content Preview", value=text_preview, height=300)
            
            # Provide download link
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=Path(file_path).name,
                mime="application/pdf"
            )
        
        # Unsupported file type
        else:
            st.warning(f"Preview not available for {file_type.upper()} files.")
            
    except Exception as e:
        logger.error(f"Error rendering file preview: {str(e)}")
        st.error(f"Error previewing file: {str(e)}")