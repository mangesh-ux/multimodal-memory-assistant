import os
from openai import OpenAI
from dotenv import load_dotenv

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
                {"role": "system", "content": "You are a helpful assistant that analyzes documents and generates metadata."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        raw = response.choices[0].message.content.strip()
        return eval(raw) if raw.startswith("{") else {}
    except Exception as e:
        print(f"[Metadata generation failed] {e}")
        return {}
