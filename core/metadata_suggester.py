import os
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_metadata(text: str, filename: str) -> dict:
    """
    Generate suggested metadata (title, tags, notes) based on the content of a file.
    """
    if not text.strip():
        return {}

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
            model="gpt-4",
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
            ]
        )

        raw_content = response.choices[0].message.content.strip()
        
        # --- Safely parse the JSON output ---
        metadata = json.loads(raw_content)

        return metadata

    except json.JSONDecodeError as e:
        print(f"[Metadata generation failed] JSON parsing error: {e}. Raw content: {raw_content}")
        return {}
    except Exception as e:
        print(f"[Metadata generation failed] An unexpected error occurred: {e}")
        return {}
