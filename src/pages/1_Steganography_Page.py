import sys
import os
import importlib.util

# Load audio_editor.py and steganography.py directly from the src/
# folder (one level up from pages/), by file path rather than relying
# on sys.path - this avoids issues with how Streamlit executes page
# scripts on some setups.
_pages_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.dirname(_pages_dir)


def _load_local_module(module_name, filename):
    if module_name in sys.modules:
        return sys.modules[module_name]
    file_path = os.path.join(_src_dir, filename)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"Expected {filename} at {file_path} but it wasn't found. "
            f"Make sure {filename} sits directly in the same folder as app.py."
        )
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module  # register so `from audio_editor import ...` inside
                                        # steganography.py resolves correctly too
    spec.loader.exec_module(module)
    return module


audio_editor_module = _load_local_module("audio_editor", "audio_editor.py")
steganography_module = _load_local_module("steganography", "steganography.py")

AudioEditor = audio_editor_module.AudioEditor
embed_message = steganography_module.embed_message
extract_message = steganography_module.extract_message

import streamlit as st
import io

st.title("Audio Steganography (hide a message via FFT)")
st.caption("Embeds a text message into the FFT magnitude spectrum. Only survives lossless "
           "WAV - do not export the result as MP3 or the hidden message will be destroyed.")

st.header("Embed a message")

source_audio = None
if "current_audio" in st.session_state:
    use_loaded = st.checkbox(
        "Use the audio currently loaded on the Audio Editor page", value=True
    )
    if use_loaded:
        source_audio = st.session_state.current_audio

if source_audio is None:
    stego_source_file = st.file_uploader(
        "Upload a WAV or MP3 file to hide a message in", type=["wav", "mp3"], key="stego_source_upload"
    )
    if stego_source_file is not None:
        source_audio = AudioEditor.load(stego_source_file)

if source_audio is not None:
    stego_message = st.text_area("Message to hide", key="stego_message")
    stego_low = st.number_input("Low frequency bound (Hz)", min_value=1.0, value=500.0, key="stego_low")
    stego_high = st.number_input("High frequency bound (Hz)", min_value=1.0, value=10000.0, key="stego_high")
    stego_step = st.number_input("Quantization step size", min_value=1.0, value=50.0, key="stego_step")

    if st.button("Embed Message"):
        if not stego_message:
            st.error("Enter a message to hide first.")
        else:
            try:
                stego_audio = embed_message(source_audio, stego_message, stego_low, stego_high, stego_step)
                st.success("Message embedded.")
                stego_buffer = io.BytesIO()
                stego_audio.save(stego_buffer, format="wav")
                stego_buffer.seek(0)
                st.audio(stego_buffer, format="audio/wav")
                st.download_button(
                    "Download stego audio (WAV only)",
                    stego_buffer,
                    file_name="stego_audio.wav",
                    mime="audio/wav",
                    key="stego_download_btn"
                )
            except ValueError as e:
                st.error(str(e))
else:
    st.info("Upload an audio file above (or load one on the Audio Editor page first) to get started.")

st.divider()
st.header("Extract a hidden message")
st.caption("Use the same frequency bounds and step size that were used to embed the message.")
stego_upload = st.file_uploader("Upload stego WAV file to decode", type=["wav"], key="stego_upload")
extract_low = st.number_input("Low frequency bound (Hz)", min_value=1.0, value=500.0, key="extract_low")
extract_high = st.number_input("High frequency bound (Hz)", min_value=1.0, value=10000.0, key="extract_high")
extract_step = st.number_input("Quantization step size", min_value=1.0, value=50.0, key="extract_step")

if stego_upload is not None and st.button("Extract Message"):
    try:
        stego_audio_loaded = AudioEditor.load(stego_upload)
        decoded = extract_message(stego_audio_loaded, extract_low, extract_high, extract_step)
        st.success(f"Decoded message: {decoded}")
    except Exception as e:
        st.error(f"Failed to extract message: {e}")