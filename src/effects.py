import numpy as np
from audio_editor import AudioEditor


def my_convolve(x, h):
    N = len(x)
    M = len(h)
    output_length = N + M - 1
    y = np.zeros(output_length)

    for k in range(M):
        y[k:k + N] += h[k] * x
    return y


def echo(audio, delay_sec, decay):
    delay_samples = int(delay_sec * audio.sample_rate)
    kernel = np.zeros(delay_samples + 1)
    kernel[0] = 1
    kernel[-1] = decay

    result_data = my_convolve(audio.data, kernel)
    return AudioEditor(result_data, audio.sample_rate)


def smooth(audio, kernel_size):
    kernel = np.ones(kernel_size) / kernel_size
    result_data = my_convolve(audio.data, kernel)
    return AudioEditor(result_data, audio.sample_rate)
