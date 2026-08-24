import streamlit as st
import matplotlib.pyplot as plt
from audio_editor import AudioEditor
from effects import echo, smooth

st.title("Audio Editor")

uploaded_file = st.file_uploader("Upload a WAV file", type=["wav"])

if uploaded_file is not None:
    audio = AudioEditor.load(uploaded_file)
    st.write("Sample rate:", audio.sample_rate)
    fig = audio.plot_waveform()
    st.pyplot(fig)

operation = st.selectbox("Choose an operation", [
    "Trim", "Reverse", "Scale", "Fade In", "Fade Out", 
    "Echo", "Smooth", "To Mono", "Normalize", "Change Speed", "Trim Silence"
])
st.write("You selected:", operation)    

if operation == "Trim":
    start = st.number_input("Start (seconds)", min_value=0.0, value=0.0)
    end = st.number_input("End (seconds)", min_value=0.0, value=1.0)

elif operation == "Reverse":
    pass

elif operation == "Scale":
    factor = st.number_input("Scale factor", min_value=0.0, value=1.0)

elif operation == "Fade In":
    duration = st.number_input("Fade duration (seconds)", min_value=0.0, value=0.5)

elif operation == "Fade Out":
    duration = st.number_input("Fade duration (seconds)", min_value=0.0, value=0.5)

elif operation == "Echo":
    delay = st.number_input("Delay (seconds)", min_value=0.0, value=0.3)
    decay = st.number_input("Decay", min_value=0.0, max_value=1.0, value=0.5)

elif operation == "Smooth":
    kernel_size = st.number_input("Kernel size", min_value=1, value=21, step=1)

elif operation == "To Mono":
    pass

elif operation == "Normalize":
    pass

elif operation == "Change Speed":
    speed_factor = st.number_input("Speed factor", min_value=0.1, value=1.0)

elif operation == "Trim Silence":
    threshold = st.number_input("Silence threshold", min_value=0.0, value=0.01)

if st.button("Apply"):
    if operation == "Trim":
        result = audio.trim(start, end)
    elif operation == "Reverse":
        result = audio.reverse()
    elif operation == "Scale":
        result = audio.scale(factor)
    elif operation == "Fade In":
        result = audio.fade_in(duration)
    elif operation == "Fade Out":
        result = audio.fade_out(duration)
    elif operation == "Echo":
        result = echo(audio, delay, decay)
    elif operation == "Smooth":
        result = smooth(audio, kernel_size)
    elif operation == "To Mono":
        result = audio.to_mono()
    elif operation == "Normalize":
        result = audio.normalize()
    elif operation == "Change Speed":
        result = audio.change_speed(speed_factor)
    elif operation == "Trim Silence":
        result = audio.trim_silence(threshold)

    st.write("Result:")
    fig = result.plot_waveform()
    st.pyplot(fig)
