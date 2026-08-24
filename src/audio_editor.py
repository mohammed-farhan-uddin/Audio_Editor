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
audio = AudioEditor.load("samples/input.wav")
mono = audio.to_mono()
print(audio.data.shape)
print(mono.data.shape)




