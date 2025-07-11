
import openai
import os
from tempfile import NamedTemporaryFile

openai.api_key = os.getenv("OPENAI_API_KEY")

def transcribe_audio(file):
    # Save the uploaded file to a temporary location
    with NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file.write(file.read())
        temp_file_path = temp_file.name

    # Use OpenAI Whisper to transcribe the audio
    with open(temp_file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file
        )
    os.remove(temp_file_path)
    return transcript['text']
