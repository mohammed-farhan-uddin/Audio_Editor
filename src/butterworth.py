"""
butterworth.py
---------------
From-scratch Butterworth filter design, following the same "derive it,
don't just call scipy" spirit as dft_demo.py.

Pipeline (matches the theory):
    1. Analog Butterworth prototype poles (Laplace domain, s-plane),
       normalized so cutoff = 1 rad/s.
    2. Scale poles by the (pre-warped) cutoff to get the analog
       low-pass OR high-pass filter H(s).
    3. Bilinear transform s = (2/T)*(1-z^-1)/(1+z^-1) to convert H(s)
       into a digital filter H(z), i.e. IIR coefficients (b, a).
    4. Apply the IIR difference equation to the signal in the time
       domain.

No scipy.signal.butter / scipy.signal.bilinear / scipy.signal.lfilter
is used -- only numpy for polynomial bookkeeping (np.poly / np.convolve),
same level of "from scratch" as the rest of this project.
"""

import numpy as np


def butterworth_poles(order):
    """
    Normalized (cutoff = 1 rad/s) analog Butterworth poles.
    These sit on the unit circle in the left half of the s-plane,
    equally spaced in angle -- that spacing is exactly what gives the
    maximally-flat magnitude response (no ripple, unlike Chebyshev).
    """
    k = np.arange(order)
    theta = np.pi * (2 * k + order + 1) / (2 * order)
    return np.exp(1j * theta)


def _bilinear_transform(b_s, a_s, sample_rate):
    """
    Convert analog filter coefficients (descending powers of s) to
    digital filter coefficients (descending powers of z^-1) using the
    bilinear transform s = c*(1-z^-1)/(1+z^-1), c = 2*sample_rate.

    Done by direct polynomial substitution: each s^k term becomes
    c^k * (1-z^-1)^k * (1+z^-1)^(N-k), expanded via repeated
    np.convolve (polynomial multiplication), then everything is summed
    over a common denominator (1+z^-1)^N.
    """
    c = 2.0 * sample_rate
    N = max(len(a_s), len(b_s)) - 1

    b_s = np.concatenate([np.zeros(N + 1 - len(b_s)), b_s])
    a_s = np.concatenate([np.zeros(N + 1 - len(a_s)), a_s])

    def transform_poly(coeffs):
        result = np.zeros(N + 1, dtype=np.complex128)
        for i, coeff in enumerate(coeffs):
            if coeff == 0:
                continue
            k = N - i  # this coeff multiplies s^k
            poly = np.array([1.0])
            for _ in range(k):
                poly = np.convolve(poly, [1.0, -1.0])   # one more (1 - z^-1) factor
            for _ in range(N - k):
                poly = np.convolve(poly, [1.0, 1.0])    # one more (1 + z^-1) factor
            result += coeff * (c ** k) * poly
        return result.real

    b_z = transform_poly(b_s)
    a_z = transform_poly(a_s)

    # Normalize so a_z[0] == 1 (standard difference-equation form)
    b_z = b_z / a_z[0]
    a_z = a_z / a_z[0]
    return b_z, a_z


def design_butterworth(order, cutoff_freq, sample_rate, btype="low"):
    """
    Design a digital Butterworth filter.

    order:       filter order N (higher = sharper cutoff, more phase distortion)
    cutoff_freq: cutoff in Hz
    sample_rate: audio sample rate in Hz
    btype:       "low" or "high"

    Returns (b, a): digital filter coefficients such that
        y[n] = b[0]*x[n] + b[1]*x[n-1] + ... - a[1]*y[n-1] - a[2]*y[n-2] - ...
    """
    if btype not in ("low", "high"):
        raise ValueError('btype must be "low" or "high"')

    T = 1.0 / sample_rate
    wc = 2 * np.pi * cutoff_freq
    # Pre-warp so the digital cutoff (after bilinear transform) lands
    # exactly at cutoff_freq instead of being frequency-warped.
    wc_warped = (2 / T) * np.tan(wc * T / 2)

    p_norm = butterworth_poles(order)  # cutoff = 1 rad/s prototype

    if btype == "low":
        poles = wc_warped * p_norm
        a_s = np.poly(poles).real          # denominator: prod(s - pole)
        b_s = np.array([wc_warped ** order])  # numerator: constant -> DC gain 1
    else:  # high-pass: s -> wc/s frequency transform on the prototype
        poles = wc_warped / p_norm
        a_s = np.poly(poles).real
        b_s = np.zeros(order + 1)
        b_s[0] = 1.0                       # numerator = s^N -> high-freq gain 1

    b_z, a_z = _bilinear_transform(b_s, a_s, sample_rate)
    return b_z, a_z


def apply_iir_filter(x, b, a):
    """
    Apply the digital filter (b, a) to signal x via the direct-form
    difference equation (a[0] is assumed already normalized to 1 by
    design_butterworth). This is O(order * len(x)) and runs as an
    explicit sample-by-sample loop since an IIR filter is inherently
    recursive (can't be vectorized the way the FIR convolution in
    effects.py can).
    """
    n_x = len(x)
    n_b = len(b)
    n_a = len(a)
    y = np.zeros(n_x)

    for n in range(n_x):
        acc = 0.0
        for i in range(n_b):
            if n - i >= 0:
                acc += b[i] * x[n - i]
        for i in range(1, n_a):
            if n - i >= 0:
                acc -= a[i] * y[n - i]
        y[n] = acc

    return y