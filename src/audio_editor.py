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





audio = AudioEditor.load("samples/input.wav")
print(audio.sample_rate)
print(audio.data)





