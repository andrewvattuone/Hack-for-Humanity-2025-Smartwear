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
from classify_command import classify_command

# Initialize wake word detection
from dotenv import load_dotenv
import os

# Load API key

load_dotenv()
ACCESS_KEY = os.getenv("PICOVOICE_API_KEY")
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

def record_command():
    """Records a command after detecting the wake word."""
    print("Listening for command...")
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
            print("Silence detected. Stopping command recording.")
            break

    # Save audio
    audio_data = b"".join(audio_frames)
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    sf.write("command_audio.wav", audio_array, sample_rate)
    print("Audio saved as command_audio.wav")

    # Transcribe the command
    r = sr.Recognizer()
    with sr.AudioFile('command_audio.wav') as source:
        r.adjust_for_ambient_noise(source)
        audio = r.record(source)
    try:
        transcription = r.recognize_google(audio)
        command = transcription.strip()
        print(f"📝 Command: {command}")
        return command
    except sr.UnknownValueError:
        print("🤷 Could not understand the command")
        return ""
    except Exception as e:
        print(f"⚠️ Exception: {e}")
        return ""

print("Waiting for wake word...")
try:
    while True:
        pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print("Wake word 'Hey Pendant' detected!")
            command = record_command()
            if command:
                print(f"Command to process: '{command}'")
                response = classify_command(command)
                print(f"🤖 Model Response:\n{response}")
                # Here you can pass `command` to the LLM function

except KeyboardInterrupt:
    print("Stopping...")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    porcupine.delete()