import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import numpy as np
import av
import queue
import threading
from voice_utils import transcribe_audio
from retriever import retrieve_relevant_chunks
from embedder import query_llm
import tempfile
import wave

st.title("MemoBrain - Live Voice Chat")

user_id = "demo_user"  # Replace with real user_id

# Queue to store audio frames
audio_queue = queue.Queue()

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recording = []
        self.lock = threading.Lock()

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray().flatten().astype(np.int16)
        with self.lock:
            self.recording.append(pcm.tobytes())
        return frame

    def get_recorded_audio(self):
        with self.lock:
            audio_data = b"".join(self.recording)
            self.recording = []
        return audio_data

st.markdown("## 🎤 Press Start and Speak")

ctx = webrtc_streamer(
    key="voice",
    mode="sendonly",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

if ctx.audio_processor:
    if st.button("🛑 Stop and Process"):
        st.info("Processing your voice input...")
        audio_data = ctx.audio_processor.get_recorded_audio()

        # Save to temp WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
            with wave.open(tmpfile.name, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(48000)
                wf.writeframes(audio_data)

            tmpfile_path = tmpfile.name

        # Transcribe using Whisper
        with open(tmpfile_path, "rb") as audio_file:
            transcript = transcribe_audio(audio_file)

        st.success("Transcription complete")
        st.markdown(f"**You said:** {transcript}")

        # Retrieve and respond using LLM
        with st.spinner("Retrieving memory..."):
            chunks = retrieve_relevant_chunks(transcript, user_id=user_id)
            context = "\\n".join(chunk.get("content", "") for chunk in chunks)

        with st.spinner("Generating answer..."):
            response = query_llm(transcript, context=context)
            st.markdown(f"**MemoBrain:** {response}")
