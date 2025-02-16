import os
import time
import wave
import struct
import speech_recognition as sr
import google.generativeai as genai
from dotenv import load_dotenv
from db_utils import insert_documents
import threading
from pydub import AudioSegment
import pyaudio

# Global flag to stop recording
stop_recording = False

def record_conversation():
    """Continuously records a conversation until the stop keyword is heard."""
    global stop_recording

    load_dotenv()

    # Configuration
    device_index = -1  # Default microphone
    sample_rate = 16000  # Adjust based on microphone capabilities
    channels = 1  # Mono audio
    frame_length = 1024  # Frame size
    output_file = "recording.wav"
    geminikey = os.getenv("GOOGLE_API_KEY")

    # Initialize PyAudio
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=frame_length)

    genai.configure(api_key=geminikey)
    model = genai.GenerativeModel('gemini-pro')

    try:
        print("🎙️ Recording... Say 'stop recording' to stop.")

        frames = []

        # Start a thread to listen for the stop keyword
        stop_thread = threading.Thread(target=listen_for_stop_keyword)
        stop_thread.start()

        # Record until stop keyword is heard
        while not stop_recording:
            data = stream.read(frame_length)
            frames.append(data)
            time.sleep(0.1)

        print("🛑 Stopping recording...")

    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save audio to WAV file
        with wave.open(output_file, 'wb') as f:
            f.setnchannels(channels)
            f.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            f.setframerate(sample_rate)
            f.writeframes(b''.join(frames))

    print(f"💾 Audio saved to {output_file}")

    # Transcribe the audio
    r = sr.Recognizer()
    with sr.AudioFile(output_file) as source:
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

def listen_for_stop_keyword():
    """Listens for the stop keyword while recording."""
    global stop_recording

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)

    while not stop_recording:
        with mic as source:
            print("🎙️ Listening for stop keyword...")
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio).lower()
            print(f"🗣️ Heard: {text}")

            if "stop recording" in text:
                stop_recording = True
                print("🛑 Stop keyword detected!")
        except sr.UnknownValueError:
            print("🤷 Couldn't understand the stop keyword.")
        except sr.RequestError as e:
            print(f"⚠️ Error with speech recognition: {e}")