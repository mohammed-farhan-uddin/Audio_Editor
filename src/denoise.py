"""
denoise.py
----------
Spectral subtraction based noise reduction.

Pipeline:
  1. STFT: split the signal into overlapping Hann-windowed frames, FFT
     each frame (noise is non-stationary, so a single whole-signal FFT
     like lowpass_filter/highpass_filter use isn't enough here).
  2. Estimate a noise profile by averaging the magnitude spectrum over
     frames drawn from a user-specified noise-only time range.
  3. Subtract alpha * noise_profile from every frame's magnitude,
     clipped to a small floor (beta * noise_profile) to avoid "musical
     noise" artifacts. Phase is left untouched.
  4. Inverse FFT each frame and reconstruct the full signal via
     overlap-add (with window-squared normalization) to avoid
     amplitude-modulation / clicking artifacts at frame boundaries.
"""

import numpy as np
from audio_editor import AudioEditor


def _hann_window(frame_size):
    return np.hanning(frame_size)


def _frame_signal(data, frame_size, hop_size):
    """Split data into overlapping frames, zero-padding the end so the
    last frame is full length. Returns (frames, padded_length)."""
    n = len(data)
    n_frames = 1 + int(np.ceil(max(0, n - frame_size) / hop_size))
    padded_len = (n_frames - 1) * hop_size + frame_size
    padded = np.zeros(padded_len)
    padded[:n] = data
    frames = np.stack([
        padded[i * hop_size: i * hop_size + frame_size]
        for i in range(n_frames)
    ])
    return frames, padded_len


def _overlap_add(frames, hop_size, frame_size, output_len):
    """Reassemble windowed frames into a signal via overlap-add,
    normalizing by the summed squared window so overlapping regions
    don't get louder/quieter than non-overlapping ones."""
    window = _hann_window(frame_size)
    output = np.zeros(output_len)
    norm = np.zeros(output_len)
    for i, frame in enumerate(frames):
        start = i * hop_size
        output[start:start + frame_size] += frame * window
        norm[start:start + frame_size] += window ** 2
    norm[norm < 1e-8] = 1e-8
    return output / norm


def estimate_noise_profile(data, sample_rate, noise_start, noise_end,
                            frame_size=2048, hop_size=512):
    """Average magnitude spectrum over a noise-only segment [noise_start, noise_end] (seconds)."""
    start_idx = int(noise_start * sample_rate)
    end_idx = int(noise_end * sample_rate)
    if end_idx - start_idx < frame_size:
        raise ValueError(
            f"Noise sample range too short - needs at least {frame_size / sample_rate:.3f} seconds."
        )
    noise_segment = data[start_idx:end_idx]
    window = _hann_window(frame_size)
    frames, _ = _frame_signal(noise_segment, frame_size, hop_size)
    magnitudes = np.abs(np.fft.rfft(frames * window, axis=1))
    return magnitudes.mean(axis=0)


def spectral_subtract_denoise(audio, noise_start, noise_end, alpha=2.0, beta=0.02,
                               frame_size=2048, hop_size=512):
    """
    audio: AudioEditor instance
    noise_start/noise_end: seconds marking a noise-only segment, used to
        estimate the noise profile
    alpha: over-subtraction factor (typical 1-2; higher = more noise
        removed, but more distortion)
    beta: spectral floor factor - fraction of the noise magnitude kept
        as a floor, avoids musical noise (typical 0.02-0.05)

    Returns a new, denoised AudioEditor.
    """
    data = audio.data
    sample_rate = audio.sample_rate

    noise_profile = estimate_noise_profile(
        data, sample_rate, noise_start, noise_end, frame_size, hop_size
    )

    window = _hann_window(frame_size)
    frames, padded_len = _frame_signal(data, frame_size, hop_size)
    windowed = frames * window

    spectrum = np.fft.rfft(windowed, axis=1)
    magnitude = np.abs(spectrum)
    phase = np.angle(spectrum)

    floor = beta * noise_profile
    subtracted = np.maximum(magnitude - alpha * noise_profile, floor)

    new_spectrum = subtracted * np.exp(1j * phase)
    new_frames = np.fft.irfft(new_spectrum, n=frame_size, axis=1)

    output = _overlap_add(new_frames, hop_size, frame_size, padded_len)
    output = output[:len(data)]

    return AudioEditor(output, sample_rate)