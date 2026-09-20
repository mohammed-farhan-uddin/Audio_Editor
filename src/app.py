import streamlit as st
import matplotlib.pyplot as plt
import io
from audio_editor import AudioEditor
from effects import echo, smooth

st.title("Audio Editor")

uploaded_file = st.file_uploader("Upload a WAV file", type=["wav"])

if uploaded_file is not None:
    if "current_audio" not in st.session_state:
        st.session_state.current_audio = AudioEditor.load(uploaded_file)
    audio = st.session_state.current_audio
    st.write("Sample rate:", audio.sample_rate)
    fig = audio.plot_waveform()
    st.pyplot(fig)

    original_buffer = io.BytesIO()
    audio.save(original_buffer)
    original_buffer.seek(0)
    st.audio(original_buffer, format="audio/wav")


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
    elif op == "Reverse":
        pass
    elif op == "Fade In":
        params["Fade In"] = {
            "duration": st.number_input("Fade In duration (seconds)", min_value=0.0, value=0.5, key="fadein_duration")
        }
    elif op == "Fade Out":
        params["Fade Out"] = {
            "duration": st.number_input("Fade Out duration (seconds)", min_value=0.0, value=0.5, key="fadeout_duration")
        }
    elif op == "Echo":
        params["Echo"] = {
            "delay": st.number_input("Delay (seconds)", min_value=0.0, value=0.3, key="echo_delay"),
            "decay": st.number_input("Decay", min_value=0.0, max_value=1.0, value=0.5, key="echo_decay")
        }
    elif op == "Smooth":
        params["Smooth"] = {
            "kernel_size": st.number_input("Kernel size", min_value=1, value=21, step=1, key="smooth_kernel")
        }
    elif op == "To Mono":
        pass
    elif op == "Normalize":
        pass
    elif op == "Change Speed":
        params["Change Speed"] = {
            "speed_factor": st.number_input("Speed factor", min_value=0.1, value=1.0, key="speed_factor")
        }
    elif op == "Trim Silence":
        params["Trim Silence"] = {
            "threshold": st.number_input("Silence threshold", min_value=0.0, value=0.01, key="silence_threshold")
        }

if st.button("Apply"):
    result = audio
    for op in operations:
        if op == "Trim":
             result = result.trim(params["Trim"]["start"], params["Trim"]["end"])
        elif op == "Scale":
            result = result.scale(params["Scale"]["factor"])
        elif op == "Reverse":
            result = result.reverse()
        elif op == "Fade In":
            result = result.fade_in(params["Fade In"]["duration"])
        elif op == "Fade Out":
            result = result.fade_out(params["Fade Out"]["duration"])
        elif op == "Echo":
            result = echo(result, params["Echo"]["delay"], params["Echo"]["decay"])
        elif op == "Smooth":
            result = smooth(result, params["Smooth"]["kernel_size"])
        elif op == "To Mono":
            result = result.to_mono()
        elif op == "Normalize":
            result = result.normalize()
        elif op == "Change Speed":
            result = result.change_speed(params["Change Speed"]["speed_factor"])
        elif op == "Trim Silence":
            result = result.trim_silence(params["Trim Silence"]["threshold"])

    st.write("Result:")
    fig = result.plot_waveform()
    st.pyplot(fig)
    

   

    buffer = io.BytesIO()
    result.save(buffer)
    buffer.seek(0)
    st.audio(buffer, format="audio/wav")
    st.download_button("Download result", buffer, file_name="edited_audio.wav", key="download_btn")
    st.session_state.current_audio = result

if st.button("Reset"):
    st.session_state.current_audio = AudioEditor.load(uploaded_file)
    st.rerun()


