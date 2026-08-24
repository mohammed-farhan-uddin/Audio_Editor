import streamlit as st
from audio_editor import AudioEditor

st.title("Audio Editor")

uploaded_file = st.file_uploader("Upload a WAV file", type=["wav"])

if uploaded_file is not None:
    st.write("File uploaded!")