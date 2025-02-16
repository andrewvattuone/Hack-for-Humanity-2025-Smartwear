import os
import time
import wave
import struct
import numpy as np
import pyaudio
import pvporcupine
import webrtcvad
import soundfile as sf
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from classify_command import classify_command

# Picovoice API Key
ACCESS_KEY = "bziOUVCEVsWrKDWAlEMC1ykpZr5MKK3THufjJACB3paF7oE3pHLPDg=="
# ACCESS_KEY = "v+kNJKIepno7qf6H2K2Ucg5HQunEska7/sRY1CY4U5C/HL9FQsPbWA=="  # Replace with your Picovoice key
wake_word_file = "Hey-Pendant.ppn"  # Ensure this file exists in the script directory

# Deepgram API Key
DEEPGRAM_API_KEY = "81558636d0b88ce3ae9fd2e74706a50981c2133c"  # Replace with your Deepgram API key

# Audio File
output_file = "recorded_audio.wav"

# Initialize PyAudio
p = pyaudio.PyAudio()
stream = p.open(rate=16000, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=1024)

# Initialize Wake Word Detection (Porcupine)
porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=[wake_word_file])

# Initialize Voice Activity Detection (VAD)
vad = webrtcvad.Vad()
vad.set_mode(3)  # Aggressive mode

def is_silence(frame, sample_rate):
    """Check if the frame is silent using VAD."""
    return not vad.is_speech(frame, sample_rate)

def record_audio():
    """Records audio until 2 seconds of silence is detected."""
    print("🎙️ Recording started... Speak now!")

    frames = []
    silent_frames = 0
    sample_rate = 16000
    frame_duration = 0.03  # 30ms
    frame_size = int(sample_rate * frame_duration)

    while True:
        data = stream.read(frame_size, exception_on_overflow=False)
        frames.append(data)

        # Convert audio data to raw PCM
        pcm_data = np.frombuffer(data, dtype=np.int16).tobytes()

        if is_silence(pcm_data, sample_rate):
            silent_frames += 1
        else:
            silent_frames = 0  # Reset silence counter if voice is detected

        if silent_frames > (2 / frame_duration):  # 2 seconds of silence
            print(" Silence detected. Stopping recording.")
            break

    save_audio(frames)
    transcribe_audio_deepgram(output_file)

def save_audio(frames):
    """Saves recorded audio to a file."""
    print(" Saving audio...")
    with wave.open(output_file, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        f.setframerate(16000)
        f.writeframes(b''.join(frames))
    print(f"Audio saved to {output_file}")

def transcribe_audio_deepgram(audio_file):
    """Transcribes the saved audio file using Deepgram API."""
    try:
        print(" Sending audio to Deepgram for transcription...")

        # STEP 1: Create a Deepgram client
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)

        # Read the audio file
        with open(audio_file, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        # STEP 2: Configure Deepgram options for transcription
        options = PrerecordedOptions(
            model="nova-3",
            smart_format=True,
           #diarize=True
        )

        # STEP 3: Call the Deepgram API
        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)

        # STEP 4: Print the response
        # command = response.get("results", {}).get("channels", [])[0].get("alternatives", [])[0].get("transcript", "")
        command = response.results.channels[0].alternatives[0].transcript
        print(f"Command to process: '{command}'")
        response = classify_command(command)
        print(f"🤖 Model Response:\n{response}")

    except Exception as e:
        print(f"Exception in Deepgram transcription: {e}")

print(" Waiting for wake word...")

try:
    while True:
        pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print(" Wake word detected! Starting recording...")
            record_audio()

except KeyboardInterrupt:
    print(" Stopping program...")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    porcupine.delete()