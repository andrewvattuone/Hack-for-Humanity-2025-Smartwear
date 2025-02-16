import pvporcupine
import pyaudio
import wave
import speech_recognition as sr
import numpy as np
import webrtcvad
import struct
import soundfile as sf
import time
from db_utils import insert_documents

# Initialize wake word detection
ACCESS_KEY = "bziOUVCEVsWrKDWAlEMC1ykpZr5MKK3THufjJACB3paF7oE3pHLPDg=="  # Get from Picovoice
porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=["Hey-Pendant.ppn"])  # Replace with your trained wake word

# Audio Stream Setup
p = pyaudio.PyAudio()
stream = p.open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=porcupine.frame_length)

# Initialize Voice Activity Detection (VAD)
vad = webrtcvad.Vad()
vad.set_mode(3)  # Aggressive mode

def is_silence(frame, sample_rate):
    """Check if frame is silence using VAD"""
    return not vad.is_speech(frame, sample_rate)

def record_audio():
    """Records audio until 2 seconds of silence is detected"""
    print("Listening... Start speaking...")
    audio_frames = []
    silent_frames = 0
    sample_rate = 16000
    frame_duration = 0.03  # 30ms
    frame_size = int(sample_rate * frame_duration)

    while True:
        data = stream.read(frame_size, exception_on_overflow=False)
        audio_frames.append(data)

        # Convert audio data to raw PCM
        pcm_data = np.frombuffer(data, dtype=np.int16).tobytes()

        if is_silence(pcm_data, sample_rate):
            silent_frames += 1
        else:
            silent_frames = 0  # Reset silence counter if voice is detected

        if silent_frames > (2 / frame_duration):  # 2 seconds of silence
            print("Silence detected. Stopping recording.")
            break

    # Save audio
    audio_data = b"".join(audio_frames)
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    sf.write("recorded_audio.wav", audio_array, sample_rate)
    print("Audio saved as recorded_audio.wav")
          
    #Transcribe the audio
    r = sr.Recognizer()
    with sr.AudioFile('recorded_audio.wav') as source:
        r.adjust_for_ambient_noise(source)
        audio = r.record(source)
    try:
        transcription = r.recognize_google(audio)  
        conversation = f"split it into sentences:\n{transcription}"
        print(f"📝 Transcription: {conversation}")
        insert_documents([conversation])
    except sr.UnknownValueError:
        print("🤷 Could not understand the audio")
    except Exception as e:
        print(f"⚠️ Exception: {e}")

print("Waiting for wake word...")
try:
    while True:
        pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print("Wake word detected!")
            record_audio()

except KeyboardInterrupt:
    print("Stopping...")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    porcupine.delete()

