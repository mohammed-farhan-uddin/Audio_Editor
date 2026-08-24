import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile





class AudioEditor:
    def __init__(self,data,sample_rate):
        self.data=data
        self.sample_rate=sample_rate
    @classmethod
    def load(cls,path):
        sample_rate, data = wavfile.read(path)
        data = data.astype(np.float64) / np.iinfo(data.dtype).max
        return cls(data,sample_rate)

    
    def trim(self,start_sec,end_sec):
        start_index = start_sec * self.sample_rate
        end_index = end_sec * self.sample_rate
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

    def save(self,path):
       clipped_data = np.clip(self.data, -1.0, 1.0)
       int_data=(self.data * 32767).astype(np.int16)
       wavfile.write(path, self.sample_rate, int_data)

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
      plt.plot(time, self.data)
      plt.xlabel("Time (s)")
      plt.ylabel("Amplitude")
      plt.title("Waveform")
      plt.show()


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
audio = AudioEditor.load("samples/input.wav")
trimmed = audio.trim_silence()
print(audio.data.shape)
print(trimmed.data.shape)
trimmed.save("silence_trimmed_test.wav")


