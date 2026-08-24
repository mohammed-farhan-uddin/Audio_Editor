import numpy as np
from audio_editor import AudioEditor

def my_convolve(x, h):
    N = len(x)
    M = len(h)
    output_length = N + M - 1
    y = np.zeros(output_length)
    
    for k in range(M):
        y[k:k+N] += h[k] * x
    return y

def convolve_stereo(data, kernel):
    left = my_convolve(data[:, 0], kernel)
    right = my_convolve(data[:, 1], kernel)
    return np.stack([left, right], axis=1)

def echo(audio, delay_sec, decay):
    delay_samples = int(delay_sec * audio.sample_rate)
    kernel = np.zeros(delay_samples + 1)
    kernel[0] = 1
    kernel[-1] = decay

    result_data = convolve_stereo(audio.data, kernel)
    return AudioEditor(result_data, audio.sample_rate)

def smooth(audio, kernel_size):
    kernel = np.ones(kernel_size) / kernel_size
    result_data = convolve_stereo(audio.data, kernel)
    return AudioEditor(result_data, audio.sample_rate)

x = np.array([1, 2, 3])
h = np.array([1, 0, 1])
result = my_convolve(x, h)
print(result)