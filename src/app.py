import streamlit as st
import matplotlib.pyplot as plt
import io
from audio_editor import AudioEditor
from effects import echo, smooth

st.title("Audio Editor")

uploaded_file = st.file_uploader("Upload a WAV or MP3 file", type=["wav", "mp3"])

if uploaded_file is not None:
    if "current_audio" not in st.session_state:
        st.session_state.current_audio = AudioEditor.load(uploaded_file)
    audio = st.session_state.current_audio
    st.write("Sample rate:", audio.sample_rate)
    fig = audio.plot_waveform()
    st.pyplot(fig)


operations = st.multiselect("Choose operations (in order)", [
    "Trim", "Reverse", "Scale", "Fade In", "Fade Out",
    "Echo", "Smooth", "To Mono", "Normalize", "Change Speed", "Trim Silence"
])

params = {}   # প্রতিটা operation এর input জমা রাখার জন্য dictionary

for op in operations:
    if op == "Trim":
        params["Trim"] = {
            "start": st.number_input("Start (seconds)", min_value=0.0, value=0.0, key="trim_start"),
            "end": st.number_input("End (seconds)", min_value=0.0, value=1.0, key="trim_end")
        }
    elif op == "Scale":
        params["Scale"] = {
            "factor": st.number_input("Scale factor", min_value=0.0, value=1.0, key="scale_factor")
        }
    # ... বাকি সব operation একই প্যাটার্নে

output_format = st.selectbox("Output format", ["wav", "mp3"])

if st.button("Apply"):
    result = audio
    for op in operations:
        if op == "Trim":
            result = result.trim(params["Trim"]["start"], params["Trim"]["end"])
        elif op == "Scale":
            result = result.scale(params["Scale"]["factor"])
        # ... বাকি সব operation একই প্যাটার্নে

    st.write("Result:")
    fig = result.plot_waveform()
    st.pyplot(fig)

    buffer = io.BytesIO()
    result.save(buffer, format=output_format)
    buffer.seek(0)

    mime = "audio/mpeg" if output_format == "mp3" else "audio/wav"
    st.audio(buffer, format=mime)

    st.download_button(
        "Download result",
        buffer,
        file_name=f"edited_audio.{output_format}",
        mime=mime,
        key="download_btn"
    )
    st.session_state.current_audio = result

if st.button("Reset"):
    st.session_state.current_audio = AudioEditor.load(uploaded_file)
    st.rerun()