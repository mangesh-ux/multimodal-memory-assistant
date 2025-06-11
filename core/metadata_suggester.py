import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import logging
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_metadata(text: str, filename: str) -> Dict[str, Any]:
    """Generate suggested metadata based on file content.
    
    Args:
        text: File content text
        filename: Name of the file
        
    Returns:
        Dictionary with suggested title, tags, and notes
    """
    if not text.strip():
        return {"title": filename, "tags": [], "notes": ""}

    # Default values in case API call fails
    default_metadata = {
        "title": filename,
        "tags": [],
        "notes": ""
    }

    prompt = (
        f"This is the content of a document titled '{filename}'.\n\n"
        f"{text[:3000]}\n\n"
        "Based on this, suggest the following metadata:\n"
        "- Title\n"
        "- Tags (as a list of short phrases)\n"
        "- A short note summarizing the essence or purpose of the document\n\n"
        "Respond in this JSON format:\n"
        '{\n'
        '  "title": "Your title here",\n'
        '  "tags": ["tag1", "tag2"],\n'
        '  "notes": "Your notes here"\n'
        '}'
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """
                You are an expert document analyst specializing in extracting structured metadata.
                Your task is to analyze the provided document content and return a JSON object
                containing specific, relevant metadata.

                The JSON object *must* conform to the following schema.
                If a field cannot be found or is not applicable, set its value to `null`.
                Ensure all keys are present.

                Example Schema:
                {
                    "title": "Your title here",
                    "tags": ["tag1", "tag2"],
                    "notes": "Your notes here"
                }
                Ensure your output is *only* the JSON object, with no conversational text or markdown wrappers.
                """},
                {"role": "user", "content": prompt}
            ],
            timeout=10  # Add timeout to prevent hanging
        )

        raw_content = response.choices[0].message.content.strip()
        
        # --- Safely parse the JSON output ---
        try:
            metadata = json.loads(raw_content)
            # Validate the structure
            if not isinstance(metadata, dict):
                logger.warning(f"Metadata generation returned non-dict: {type(metadata)}")
                return default_metadata
                
            # Ensure all required keys exist
            for key in ["title", "tags", "notes"]:
                if key not in metadata:
                    metadata[key] = default_metadata[key]
                    
            # Ensure tags is a list
            if not isinstance(metadata.get("tags", []), list):
                metadata["tags"] = []
                
            return metadata

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}. Raw content: {raw_content}")
            return default_metadata
            
    except Exception as e:
        logger.error(f"Metadata generation failed: {str(e)}")
        return default_metadata
