import streamlit as st
import matplotlib.pyplot as plt
import io
from audio_editor import AudioEditor
from effects import echo, smooth
from steganography import embed_message, extract_message

st.title("Audio Editor")

uploaded_file = st.file_uploader("Upload a WAV or MP3 file", type=["wav", "mp3"])

if uploaded_file is not None:
    if "current_audio" not in st.session_state:
        st.session_state.current_audio = AudioEditor.load(uploaded_file)
    audio = st.session_state.current_audio
    st.write("Sample rate:", audio.sample_rate)
    fig = audio.plot_waveform()
    st.pyplot(fig)

    if st.checkbox("Show frequency spectrum (FFT)", key="show_spectrum_original"):
        spec_fig = audio.plot_spectrum()
        st.pyplot(spec_fig)

    original_buffer = io.BytesIO()
    audio.save(original_buffer)
    original_buffer.seek(0)
    st.audio(original_buffer, format="audio/wav")

    operations = st.multiselect("Choose operations (in order)", [
        "Trim", "Reverse", "Scale", "Fade In", "Fade Out",
        "Echo", "Smooth", "To Mono", "Normalize", "Change Speed", "Trim Silence",
        "Low-Pass Filter", "High-Pass Filter",
        "Butterworth Low-Pass", "Butterworth High-Pass"
    ])

    params = {}

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
        elif op == "Low-Pass Filter":
            params["Low-Pass Filter"] = {
                "cutoff": st.number_input("Cutoff frequency (Hz) - keep below this", min_value=1.0, value=1000.0, key="lowpass_cutoff")
            }
        elif op == "High-Pass Filter":
            params["High-Pass Filter"] = {
                "cutoff": st.number_input("Cutoff frequency (Hz) - keep above this", min_value=1.0, value=1000.0, key="highpass_cutoff")
            }
        elif op == "Butterworth Low-Pass":
            params["Butterworth Low-Pass"] = {
                "cutoff": st.number_input("Cutoff frequency (Hz)", min_value=1.0, value=1000.0, key="butter_lp_cutoff"),
                "order": st.number_input("Filter order", min_value=1, max_value=10, value=4, step=1, key="butter_lp_order")
            }
        elif op == "Butterworth High-Pass":
            params["Butterworth High-Pass"] = {
                "cutoff": st.number_input("Cutoff frequency (Hz)", min_value=1.0, value=1000.0, key="butter_hp_cutoff"),
                "order": st.number_input("Filter order", min_value=1, max_value=10, value=4, step=1, key="butter_hp_order")
            }

    output_format = st.selectbox("Output format", ["wav", "mp3"])

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
            elif op == "Low-Pass Filter":
                result = result.lowpass_filter(params["Low-Pass Filter"]["cutoff"])
            elif op == "High-Pass Filter":
                result = result.highpass_filter(params["High-Pass Filter"]["cutoff"])
            elif op == "Butterworth Low-Pass":
                result = result.butterworth_lowpass(
                    params["Butterworth Low-Pass"]["cutoff"],
                    int(params["Butterworth Low-Pass"]["order"])
                )
            elif op == "Butterworth High-Pass":
                result = result.butterworth_highpass(
                    params["Butterworth High-Pass"]["cutoff"],
                    int(params["Butterworth High-Pass"]["order"])
                )

        st.write("Result:")
        fig = result.plot_waveform()
        st.pyplot(fig)

        if st.checkbox("Show frequency spectrum of result (FFT)", key="show_spectrum_result"):
            spec_fig = result.plot_spectrum()
            st.pyplot(spec_fig)

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

    st.divider()
    st.header("Audio Steganography (hide a message via FFT)")
    st.caption("Embeds a text message into the FFT magnitude spectrum. Only survives lossless "
               "WAV — do not export the result as MP3 or the hidden message will be destroyed.")

    st.subheader("Embed a message")
    stego_message = st.text_area("Message to hide", key="stego_message")
    stego_low = st.number_input("Low frequency bound (Hz)", min_value=1.0, value=500.0, key="stego_low")
    stego_high = st.number_input("High frequency bound (Hz)", min_value=1.0, value=10000.0, key="stego_high")
    stego_step = st.number_input("Quantization step size", min_value=1.0, value=50.0, key="stego_step")

    if st.button("Embed Message"):
        if not stego_message:
            st.error("Enter a message to hide first.")
        else:
            try:
                stego_audio = embed_message(audio, stego_message, stego_low, stego_high, stego_step)
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

    st.subheader("Extract a hidden message")
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