import openai
import os
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def embed_text_list(chunks: list[str], model="text-embedding-3-small") -> list[list[float]]:
    if not chunks:
        return []

    response = openai.embeddings.create(
        input=chunks,
        model=model
    )

    return [r.embedding for r in response.data]
