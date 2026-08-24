from audio_editor import AudioEditor
from effects import echo

audio = AudioEditor.load("samples/input.wav")
short_clip = audio.trim(0, 6)          # শুধু ১ সেকেন্ড
echoed = echo(short_clip, 0.1, 0.5)     # ছোট delay
echoed.save("echo_test.wav")
