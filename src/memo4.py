import os
import time
import wave
import struct
import numpy as np
import pyaudio
import pvporcupine
import soundfile as sf
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from classify_command import classify_command
from flask import Flask, render_template
from threading import Thread
from dotenv import load_dotenv

load_dotenv()
ACCESS_KEY = os.getenv("PICOVOICE_API_KEY")
wake_word_file = "Hey-Pendant.ppn"

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

output_file = "recorded_audio.wav"

p = pyaudio.PyAudio()
stream = p.open(rate=16000, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=1024)

porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=[wake_word_file])

app = Flask(__name__)
shared_response = {"value": None}

def record_audio():
    print("Recording started... Speak now!")

    frames = []
    sample_rate = 16000
    frame_duration = 0.03
    frame_size = int(sample_rate * frame_duration)

    start_time = time.time()

    while time.time() - start_time < 8:
        data = stream.read(frame_size, exception_on_overflow=False)
        frames.append(data)

    print("5 seconds elapsed. Stopping recording.")
    save_audio(frames)
    transcribe_audio_deepgram(output_file)

def save_audio(frames):
    print("Saving audio...")
    with wave.open(output_file, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        f.setframerate(16000)
        f.writeframes(b''.join(frames))
    print(f"Audio saved to {output_file}")

def transcribe_audio_deepgram(audio_file):
    try:
        print("Sending audio to Deepgram for transcription...")

        deepgram = DeepgramClient(DEEPGRAM_API_KEY)

        with open(audio_file, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        options = PrerecordedOptions(
            model="nova-3",
            smart_format=True,
        )

        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)

        command = response.results.channels[0].alternatives[0].transcript
        print(f"Command to process: '{command}'")
        response = classify_command(command)
        print(f"Model Response:\n{response}")
        shared_response["value"] = response

    except Exception as e:
        print(f"Exception in Deepgram transcription: {e}")

@app.route('/')
def home():
    if shared_response["value"] is None:
        message = "Listening for the wake word..."
    else:
        message = f"Response: {shared_response['value']}"

    return render_template('page.html', message=message)

def run_audio_loop():
    print("Waiting for wake word...")

    try:
        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print("Wake word detected! Starting recording...")
                record_audio()

    except KeyboardInterrupt:
        print("Stopping program...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        porcupine.delete()

if __name__ == '__main__':
    Thread(target=run_audio_loop, daemon=True).start()
    app.run(debug=True, threaded=True)
