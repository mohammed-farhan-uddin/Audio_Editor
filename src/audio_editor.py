import subprocess
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from butterworth import design_butterworth, apply_iir_filter


class AudioEditor:
    def __init__(self, data, sample_rate):
        self.data = data
        self.sample_rate = sample_rate

    @classmethod
    def load(cls, file, filename=None):
        """
        file: either a path string, or a file-like object (e.g. Streamlit's UploadedFile)
        filename: needed if `file` is a file-like object without a .name attribute
        """
        name = filename or getattr(file, "name", None) or (file if isinstance(file, str) else "")
        is_wav = str(name).lower().endswith(".wav")

        if is_wav:
            sample_rate, data = wavfile.read(file)
            data = data.astype(np.float64) / np.iinfo(data.dtype).max
            if data.ndim == 2:
                data = data.mean(axis=1)  # stereo -> mono
            return cls(data, sample_rate)
        else:
            return cls._load_via_ffmpeg(file)

    @classmethod
    def _load_via_ffmpeg(cls, file, sample_rate=44100):
        if isinstance(file, str):
            with open(file, "rb") as f:
                input_bytes = f.read()
        else:
            file.seek(0)
            input_bytes = file.read()

        cmd = [
            "ffmpeg", "-i", "pipe:0",
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", "1",   # force mono directly from ffmpeg
            "-loglevel", "error",
            "pipe:1"
        ]
        result = subprocess.run(cmd, input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()}")

        raw = np.frombuffer(result.stdout, dtype=np.int16)
        data = raw.astype(np.float64) / 32768.0

        return cls(data, sample_rate)

    def trim(self, start_sec, end_sec):
        start_index = int(start_sec * self.sample_rate)
        end_index = int(end_sec * self.sample_rate)
        return AudioEditor(self.data[start_index:end_index], self.sample_rate)

    def reverse(self):
        return AudioEditor(self.data[::-1], self.sample_rate)

    def scale(self, factor):
        data = self.data * factor
        return AudioEditor(data, self.sample_rate)

    @staticmethod
    def join(clips):
        combined_data = np.concatenate([clip.data for clip in clips])
        return AudioEditor(combined_data, clips[0].sample_rate)

    def fade_in(self, duration_sec):
        n = int(duration_sec * self.sample_rate)
        ramp = np.linspace(0, 1, n)
        data = self.data.copy()
        data[:n] = data[:n] * ramp
        return AudioEditor(data, self.sample_rate)

    def fade_out(self, duration_sec):
        n = int(duration_sec * self.sample_rate)
        ramp = np.linspace(1, 0, n)
        data = self.data.copy()
        data[-n:] = data[-n:] * ramp
        return AudioEditor(data, self.sample_rate)

    def save(self, path, format="wav"):
        """
        path: file path or file-like object (e.g. io.BytesIO for Streamlit)
        format: "wav" or "mp3"
        """
        clipped_data = np.clip(self.data, -1.0, 1.0)
        int_data = (clipped_data * 32767).astype(np.int16)

        if format == "wav":
            wavfile.write(path, self.sample_rate, int_data)
        elif format == "mp3":
            self._save_as_mp3(int_data, path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _save_as_mp3(self, int_data, path):
        # mono data now, so channels is always 1
        channels = int_data.shape[1] if int_data.ndim > 1 else 1
        raw_bytes = int_data.tobytes()

        cmd = [
            "ffmpeg", "-y",
            "-f", "s16le",
            "-ar", str(self.sample_rate),
            "-ac", str(channels),
            "-i", "pipe:0",
            "-f", "mp3",
            "-loglevel", "error",
            "pipe:1"
        ]
        result = subprocess.run(cmd, input=raw_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()}")

        mp3_bytes = result.stdout

        if isinstance(path, str):
            with open(path, "wb") as f:
                f.write(mp3_bytes)
        else:
            path.write(mp3_bytes)

    def to_mono(self):
        if self.data.ndim == 2:
            return AudioEditor(self.data.mean(axis=1), self.sample_rate)
        return AudioEditor(self.data, self.sample_rate)

    def normalize(self):
        max_val = np.max(np.abs(self.data))
        normalized_data = self.data / max_val
        return AudioEditor(normalized_data, self.sample_rate)

    def mix(self, other):
        min_length = min(len(self.data), len(other.data))
        mixed_data = self.data[:min_length] + other.data[:min_length]
        return AudioEditor(mixed_data, self.sample_rate)

    def change_speed(self, speed_factor):
        old_length = len(self.data)
        new_length = int(old_length / speed_factor)
        old_indices = np.arange(old_length)
        new_indices = np.linspace(0, old_length - 1, new_length)
        new_data = np.interp(new_indices, old_indices, self.data)
        return AudioEditor(new_data, self.sample_rate)

    def trim_silence(self, threshold=0.01):
        amplitude = np.abs(self.data)
        loud_indices = np.where(amplitude > threshold)[0]

        if len(loud_indices) == 0:
            return AudioEditor(self.data, self.sample_rate)

        start = loud_indices[0]
        end = loud_indices[-1]
        trimmed_data = self.data[start:end + 1]

        return AudioEditor(trimmed_data, self.sample_rate)

    def plot_waveform(self, max_points=10000):
        duration = len(self.data) / self.sample_rate
        time = np.linspace(0, duration, len(self.data))

        # Downsample for plotting speed only (does not affect self.data)
        if len(self.data) > max_points:
            step = len(self.data) // max_points
            plot_time = time[::step]
            plot_data = self.data[::step]
        else:
            plot_time = time
            plot_data = self.data

        fig, ax = plt.subplots()
        ax.plot(plot_time, plot_data)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude")
        ax.set_title("Waveform")
        return fig

    # ------------------------------------------------------------------
    # DFT / FFT based features
    # ------------------------------------------------------------------
    def plot_spectrum(self, max_freq=5000):
        """Frequency-domain view using FFT (np.fft.rfft).
        max_freq limits the x-axis so low-frequency detail isn't
        squeezed into a corner of the plot."""
        n = len(self.data)
        freqs = np.fft.rfftfreq(n, d=1 / self.sample_rate)
        magnitude = np.abs(np.fft.rfft(self.data))

        fig, ax = plt.subplots()
        ax.plot(freqs, magnitude)
        ax.set_xlim(0, max_freq)
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Magnitude")
        ax.set_title("Frequency Spectrum (FFT)")
        return fig

    def lowpass_filter(self, cutoff_freq):
        """Remove frequencies above cutoff_freq using FFT (frequency-domain filtering)."""
        n = len(self.data)
        freqs = np.fft.rfftfreq(n, d=1 / self.sample_rate)
        spectrum = np.fft.rfft(self.data)
        spectrum[freqs > cutoff_freq] = 0
        filtered = np.fft.irfft(spectrum, n=n)
        return AudioEditor(filtered, self.sample_rate)

    def highpass_filter(self, cutoff_freq):
        """Remove frequencies below cutoff_freq using FFT (frequency-domain filtering)."""
        n = len(self.data)
        freqs = np.fft.rfftfreq(n, d=1 / self.sample_rate)
        spectrum = np.fft.rfft(self.data)
        spectrum[freqs < cutoff_freq] = 0
        filtered = np.fft.irfft(spectrum, n=n)
        return AudioEditor(filtered, self.sample_rate)

    # ------------------------------------------------------------------
    # Butterworth filters (Laplace-domain design -> bilinear transform
    # -> IIR difference equation). See butterworth.py. Unlike
    # lowpass_filter/highpass_filter above (hard FFT bin zeroing), these
    # are true analog-derived filters with a smooth, maximally-flat
    # roll-off controlled by `order`.
    # ------------------------------------------------------------------
    def butterworth_lowpass(self, cutoff_freq, order=4):
        b, a = design_butterworth(order, cutoff_freq, self.sample_rate, btype="low")
        filtered = apply_iir_filter(self.data, b, a)
        return AudioEditor(filtered, self.sample_rate)

    def butterworth_highpass(self, cutoff_freq, order=4):
        b, a = design_butterworth(order, cutoff_freq, self.sample_rate, btype="high")
        filtered = apply_iir_filter(self.data, b, a)
        return AudioEditor(filtered, self.sample_rate)