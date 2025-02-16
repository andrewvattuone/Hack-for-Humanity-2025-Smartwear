import os
import time
import wave
import struct
import speech_recognition as sr
from pvrecorder import PvRecorder
import google.generativeai as genai
from dotenv import load_dotenv
from db_utils import insert_documents
import threading
from pydub import AudioSegment

# Global flag to stop recording
stop_recording = False

import pyaudio

import pyaudio

p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"{info['name']}: {info['defaultSampleRate']} Hz")
p.terminate()


def record_conversation():
    """Continuously records a conversation until the stop keyword is heard."""
    global stop_recording

    load_dotenv()

    # Configuration
    device_index = -1  # Default microphone
    frame_length = 512  # 32ms of 16kHz audio
    output_file = "recording.wav"
    geminikey = os.getenv("GOOGLE_API_KEY")

    # Initialize Picovoice Recorder
    recorder = PvRecorder(frame_length=frame_length, device_index=device_index)
    genai.configure(api_key=geminikey)
    model = genai.GenerativeModel('gemini-pro')

    try:
        recorder.start()
        print("🎙️ Recording... Say 'stop recording' to stop.")

        frames = []

        # Start a thread to listen for the stop keyword
        stop_thread = threading.Thread(target=listen_for_stop_keyword)
        stop_thread.start()

        # Record until stop keyword is heard
        while not stop_recording:
            frame = recorder.read()
            frames.extend(frame)
            time.sleep(0.1)

        print("🛑 Stopping recording...")

    finally:
        recorder.stop()
        recorder.delete()

        # Save audio to WAV file

        with wave.open(output_file, 'w') as f:
            f.setparams((1, 2, 48000, 0, 'NONE', 'NONE'))
            f.writeframes(struct.pack("h" * len(frames), *frames))

    # print(f"💾 Audio saved to {output_file}")
    # correct_sample_rate = 44100  # Adjust this based on your microphone's sample rate
    # audio = AudioSegment.from_wav(output_file)
    # audio = audio.set_frame_rate(correct_sample_rate)
    # audio.export("fixed_recording.wav", format="wav")

    # print("🔄 Audio re-sampled to correct rate and saved to fixed_recording.wav")

    print(f"Audio saved to {output_file}")
    r=sr.Recognizer()
    with sr.AudioFile("recording.wav") as source:
        audio = r.record(source)
    try:
        s = r.recognize_google(audio)
        print("HI")
        conversation = f"split it into sentences:\n{s}"
        insert_documents([conversation])
    except sr.UnknownValueError:
        print("Could not understand audio")
        #print("Text: "+s)
    except Exception as e:
        print("Exception: "+str(e))

    

    # Transcribe audio
    # recognizer = sr.Recognizer()
    # with sr.AudioFile(output_file) as source:
    #     audio = recognizer.record(source)

    # try:
    #     transcription = recognizer.recognize_google(audio)
    #     conversation = f"split it into sentences:\n{transcription}"
    #     print(f"📝 Transcription: {conversation}")

    #     # Insert conversation into database
    #     insert_documents([conversation])

    # except sr.UnknownValueError:
    #     print("🤷 Could not understand audio")
    # except Exception as e:
    #     print(f"⚠️ Exception during transcription: {e}")

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