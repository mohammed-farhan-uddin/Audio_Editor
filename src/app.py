import streamlit as st
import matplotlib.pyplot as plt
from audio_editor import AudioEditor

st.title("Audio Editor")

uploaded_file = st.file_uploader("Upload a WAV file", type=["wav"])

if uploaded_file is not None:
    audio = AudioEditor.load(uploaded_file)
    st.write("Sample rate:", audio.sample_rate)
    fig = audio.plot_waveform()
    st.pyplot(fig)