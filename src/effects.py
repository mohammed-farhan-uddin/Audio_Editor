import numpy as np
from audio_editor import AudioEditor


def my_convolve(x, h):
    """
    Linear convolution via the FFT (convolution theorem):
        convolve(x, h) == ifft(fft(x, L) * fft(h, L))
    where L = len(x) + len(h) - 1 is chosen so the circular convolution
    the FFT computes doesn't wrap around and matches true linear
    convolution exactly.

    The old version of this function looped over every kernel index k
    and did y[k:k+N] += h[k]*x - that's O(N*M) even when h is mostly
    zero (e.g. echo's kernel, which is length delay_samples+1 but has
    only 2 non-zero entries). FFT convolution costs O((N+M) log(N+M))
    regardless of how sparse or dense h is, which is what makes echo()
    on a several-second clip go from many seconds down to well under 1.
    """
    N = len(x)
    M = len(h)
    output_length = N + M - 1

    X = np.fft.rfft(x, n=output_length)
    H = np.fft.rfft(h, n=output_length)
    y = np.fft.irfft(X * H, n=output_length)
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