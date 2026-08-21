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
    
        




audio = AudioEditor.load("samples/input.wav")
trimmed = audio.trim(2, 5)
reversed_clip = trimmed.reverse()
print(reversed_clip.data.shape)





