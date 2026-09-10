import subprocess
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment

class AudioEditor:
    def __init__(self,data,sample_rate):
        self.data=data
        self.sample_rate=sample_rate
    @classmethod
    def load(cls, file, filename=None):
        """
        file: either a path string, or a file-like object (e.g. Streamlit's UploadedFile)
        filename: needed if `file` is a file-like object without a .name attribute
        """
        # Figure out the extension
        name = filename or getattr(file, "name", None) or (file if isinstance(file, str) else "")
        is_wav = str(name).lower().endswith(".wav")

        if is_wav:
            sample_rate, data = wavfile.read(file)
            data = data.astype(np.float64) / np.iinfo(data.dtype).max
            return cls(data, sample_rate)
        else:
            return cls._load_via_ffmpeg(file)

    @classmethod
    def _load_via_ffmpeg(cls, file, sample_rate=44100, channels=2):
        # Get raw bytes whether `file` is a path or a file-like object
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
            "-ac", str(channels),
            "-loglevel", "error",
            "pipe:1"
        ]
        result = subprocess.run(cmd, input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()}")

        raw = np.frombuffer(result.stdout, dtype=np.int16)
        raw = raw.reshape((-1, channels))
        data = raw.astype(np.float64) / 32768.0

        return cls(data, sample_rate)

    
    def trim(self,start_sec,end_sec):
        start_index = int(start_sec * self.sample_rate)
        end_index = int(end_sec * self.sample_rate)
        return AudioEditor(self.data[start_index:end_index],self.sample_rate)

    
    def reverse(self):
        return AudioEditor(self.data[::-1],self.sample_rate)

    
    def scale(self,factor):
        data=self.data*factor
        return AudioEditor(data,self.sample_rate)

    @staticmethod
    def join(clips):
        combined_data = np.concatenate([clip.data for clip in clips])
        return AudioEditor(combined_data, clips[0].sample_rate)

    def fade_in(self,duration_sec):
        n = int(duration_sec * self.sample_rate)
        ramp=np.linspace(0,1,n)
        data=self.data.copy()
        data[:n]=data[:n] * ramp[:,None]
        return AudioEditor(data,self.sample_rate)

    def fade_out(self,duration_sec):
        n = int(duration_sec * self.sample_rate)
        ramp=np.linspace(1,0,n)
        data=self.data.copy()
        data[-n:]=data[-n:] * ramp[:,None]
        return AudioEditor(data,self.sample_rate)

    def save(self, path, format="wav"):
    
    #path: file path or file-like object (e.g. io.BytesIO for Streamlit)
    #format: "wav" or "mp3"
    
       clipped_data = np.clip(self.data, -1.0, 1.0)
       int_data = (clipped_data * 32767).astype(np.int16)

       if format == "wav":
        wavfile.write(path, self.sample_rate, int_data)

       elif format == "mp3":
        self._save_as_mp3(int_data, path)

       else:
        raise ValueError(f"Unsupported format: {format}")

    def _save_as_mp3(self, int_data, path):
    # int_data shape: (n_samples, n_channels) or (n_samples,) if mono
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

    # Write to a real path or a file-like object (e.g. io.BytesIO)
       if isinstance(path, str):
        with open(path, "wb") as f:
            f.write(mp3_bytes)
       else:
        path.write(mp3_bytes)

    def to_mono(self):
      mono_data = self.data.mean(axis=1)
      return AudioEditor(mono_data, self.sample_rate)

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
    
      left = np.interp(new_indices, old_indices, self.data[:, 0])
      right = np.interp(new_indices, old_indices, self.data[:, 1])
      new_data = np.stack([left, right], axis=1)
    
      return AudioEditor(new_data, self.sample_rate)   

    def trim_silence(self, threshold=0.01):
      amplitude = np.abs(self.data).max(axis=1)   # প্রতিটা sample এর loudness (stereo থেকে একটা সংখ্যা)
      loud_indices = np.where(amplitude > threshold)[0]   # কোন কোন index এ শব্দ আছে

      if len(loud_indices) == 0:
        return AudioEditor(self.data, self.sample_rate)   # পুরোটাই silence হলে অপরিবর্তিত রাখো

      start = loud_indices[0]
      end = loud_indices[-1]
      trimmed_data = self.data[start:end+1]

      return AudioEditor(trimmed_data, self.sample_rate)   

    

    def plot_waveform(self):
      duration = len(self.data) / self.sample_rate
      time = np.linspace(0, duration, len(self.data))
      fig, ax = plt.subplots()
      ax.plot(time, self.data)
      ax.set_xlabel("Time (s)")
      ax.set_ylabel("Amplitude")
      ax.set_title("Waveform")
      return fig


# join

# audio = AudioEditor.load("samples/input.wav")
# clip1 = audio.trim(0, 2)
# clip2 = audio.trim(2, 4)
# joined = AudioEditor.join([clip1, clip2])
# print(joined.data.shape)

# fade_in

# audio = AudioEditor.load("samples/input.wav")
# faded = audio.fade_in(2)
# print(faded.data[0])        # প্রথম sample
# print(audio.data[0])        # আগের (fade করার আগের) প্রথম sample

# audio = AudioEditor.load("samples/input.wav")
# faded = audio.fade_out(2)
# print(faded.data[-1])        
# print(audio.data[-1]) 

##save
# audio = AudioEditor.load("samples/input.wav")
# reversed_clip = audio.reverse()
# scale_clip = audio.fade_in(2)
# scale_clip=scale_clip.fade_out(2)
# scale_clip.save("output_test.wav")
# audio = AudioEditor.load("samples/input.wav")
# audio.plot_waveform()
# audio = AudioEditor.load("samples/input.wav")
# mono = audio.to_mono()
# print(audio.data.shape)
# print(mono.data.shape)
# audio = AudioEditor.load("samples/input.wav")
# scaled_down = audio.scale(0.3)     # আগে ভলিউম কমাও (একটা quiet audio simulate করার জন্য)
# normalized = scaled_down.normalize()
# print(scaled_down.data.max())
# print(normalized.data.max())
# audio = AudioEditor.load("samples/input.wav")
# clip1 = audio.trim(0, 5)
# clip2 = audio.trim(5, 10)
# mixed = clip1.mix(clip2)
# mixed.save("mix_test.wav")
# audio = AudioEditor.load("samples/input.wav")
# fast = audio.change_speed(1.5)
# fast.save("fast_test.wav")
# slow = audio.change_speed(0.7)
# slow.save("slow_test.wav")
audio = AudioEditor.load("samples/input.mp3")
trimmed = audio.trim_silence()
print(audio.data.shape)
print(trimmed.data.shape)
trimmed.save("silence_trimmed_test.wav")


