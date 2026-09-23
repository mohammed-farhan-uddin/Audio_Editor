"""
steganography.py
-----------------
Hide a text message inside an audio signal using its FFT magnitude
spectrum (frequency-domain steganography).

Technique: Quantization Index Modulation (QIM). For a chosen band of
frequency bins, each bin's magnitude is rounded to the nearest multiple
of a step size Q, and the parity (even/odd multiple) of that rounding
encodes one bit. This is more robust than flipping the raw
least-significant-bit of a float, since it snaps the magnitude to a
well-defined quantization grid.

Only the magnitude is touched -- phase is left untouched -- which keeps
the audible change small (roughly the size of the quantization step Q).

IMPORTANT: this only survives lossless re-encoding. Saving the stego
audio as MP3 (lossy) will destroy the embedded magnitudes, so the
result must be kept/downloaded as WAV.
"""

import numpy as np
from audio_editor import AudioEditor


def _text_to_bits(text):
    data = text.encode("utf-8")
    length = len(data)
    length_bits = [int(b) for b in format(length, "032b")]
    bits = []
    for byte in data:
        bits.extend(int(b) for b in format(byte, "08b"))
    return length_bits + bits


def _bits_to_text(bits):
    length = int("".join(str(b) for b in bits[:32]), 2)
    message_bits = bits[32:32 + length * 8]
    byte_vals = []
    for i in range(0, len(message_bits), 8):
        byte_bits = message_bits[i:i + 8]
        byte_vals.append(int("".join(str(b) for b in byte_bits), 2))
    return bytes(byte_vals).decode("utf-8", errors="replace")


def _select_bins(freqs, low_freq, high_freq):
    return np.where((freqs >= low_freq) & (freqs <= high_freq))[0]


def embed_message(audio, message, low_freq=500.0, high_freq=10000.0, step=50.0):
    """
    audio:   AudioEditor instance (carrier)
    message: text to hide
    low_freq/high_freq: usable frequency band for embedding (Hz) --
        avoid very low frequencies (audible) and very high ones (not
        robust to lossy re-encoding)
    step: QIM quantization step size (bigger = more robust to noise,
        but slightly more audible)

    Returns a new AudioEditor with the message embedded.
    """
    n = len(audio.data)
    spectrum = np.fft.rfft(audio.data)
    freqs = np.fft.rfftfreq(n, d=1 / audio.sample_rate)
    bin_indices = _select_bins(freqs, low_freq, high_freq)

    bits = _text_to_bits(message)

    if len(bits) > len(bin_indices):
        raise ValueError(
            f"Message too long: needs {len(bits)} bits (incl. 32-bit length header) "
            f"but only {len(bin_indices)} usable frequency bins are available in "
            f"{low_freq}-{high_freq} Hz. Shorten the message or widen the frequency range."
        )

    magnitudes = np.abs(spectrum)
    phases = np.angle(spectrum)

    for bit, idx in zip(bits, bin_indices):
        k = round(magnitudes[idx] / step)
        if k % 2 != bit:
            k += 1
        magnitudes[idx] = k * step

    new_spectrum = magnitudes * np.exp(1j * phases)
    stego_data = np.fft.irfft(new_spectrum, n=n)

    return AudioEditor(stego_data, audio.sample_rate)


def extract_message(audio, low_freq=500.0, high_freq=10000.0, step=50.0):
    """
    audio: AudioEditor instance (stego carrier, must be lossless/WAV --
        MP3 re-encoding destroys the embedded bits)

    low_freq/high_freq/step MUST match the values used in embed_message,
    otherwise the wrong bins/grid are read and decoding will fail or
    produce garbage.

    Returns the decoded text message.
    """
    n = len(audio.data)
    spectrum = np.fft.rfft(audio.data)
    freqs = np.fft.rfftfreq(n, d=1 / audio.sample_rate)
    bin_indices = _select_bins(freqs, low_freq, high_freq)

    if len(bin_indices) < 32:
        raise ValueError("Not enough usable frequency bins to read a message length header.")

    magnitudes = np.abs(spectrum)

    length_bits = [round(magnitudes[idx] / step) % 2 for idx in bin_indices[:32]]
    length = int("".join(str(b) for b in length_bits), 2)

    total_bits_needed = 32 + length * 8
    if total_bits_needed > len(bin_indices) or length < 0:
        raise ValueError(
            "Decoded length header looks invalid. Make sure this audio actually has a "
            "message embedded, and that low_freq/high_freq/step match the encode settings."
        )

    bits = [round(magnitudes[idx] / step) % 2 for idx in bin_indices[:total_bits_needed]]
    return _bits_to_text(bits)