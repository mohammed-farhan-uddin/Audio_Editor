from audio_editor import AudioEditor
from effects import echo,smooth

# audio = AudioEditor.load("samples/input.wav")
# echoed = echo(audio, 0.1, 2)     # ছোট delay
# echoed.save("echo_test.wav")

audio = AudioEditor.load("samples/input.wav")
smoothed = smooth(audio, 21)
smoothed.save("smooth_test.wav")