
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
sample_rate, data = wavfile.read("samples/input.wav")


data = data.astype(np.float64) / np.iinfo(data.dtype).max

duration=len(data)/sample_rate
time = np.linspace(0,duration,len(data))

plt.plot(time, data)
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.title("Waveform")
plt.show()