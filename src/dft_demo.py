"""
dft_demo.py
-----------
A from-scratch (naive) DFT implementation, for demonstration purposes.

The Discrete Fourier Transform converts a time-domain signal into its
frequency-domain representation. The direct/naive way to compute it is:

    X[k] = sum_{n=0}^{N-1} x[n] * exp(-2j * pi * k * n / N)

This is a straightforward translation of the formula into code, but it is
O(N^2) -- for every output frequency k, we loop over every input sample n.
For an audio signal with hundreds of thousands of samples, this is far too
slow to run on the whole signal (it would take minutes/hours).

The Fast Fourier Transform (FFT) computes the exact same result in
O(N log N) using a divide-and-conquer algorithm (Cooley-Tukey), which is
why real applications (including the rest of this project, in
`plot_spectrum`, `lowpass_filter`, `highpass_filter`) use `np.fft.fft`
instead of a naive DFT.

This file exists to demonstrate understanding of the underlying algorithm.
Use `naive_dft` only on small inputs (a few hundred/thousand samples).
"""

import numpy as np


def naive_dft(x):
    """
    Compute the DFT of 1D array x using the direct O(N^2) formula.
    Only practical for small N (e.g. a few thousand samples at most).
    """
    N = len(x)
    n = np.arange(N)
    k = n.reshape((N, 1))
    exponent = np.exp(-2j * np.pi * k * n / N)
    return np.dot(exponent, x)


if __name__ == "__main__":
    # Quick correctness check: naive_dft should match numpy's FFT
    import time

    x = np.random.randn(512)  # small signal, since naive DFT is O(N^2)

    start = time.time()
    X_naive = naive_dft(x)
    naive_time = time.time() - start

    start = time.time()
    X_fft = np.fft.fft(x)
    fft_time = time.time() - start

    print("Naive DFT matches FFT:", np.allclose(X_naive, X_fft))
    print(f"Naive DFT time (N={len(x)}): {naive_time:.6f}s")
    print(f"FFT time       (N={len(x)}): {fft_time:.6f}s")