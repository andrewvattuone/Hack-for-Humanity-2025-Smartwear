import os
import time
import wave
import struct
import numpy as np
import pyaudio
import webrtcvad
import soundfile as sf
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from db_utils import insert_documents
from dotenv import load_dotenv

# Deepgram API Key
def record_conversation():
    load_dotenv()
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

    # Audio File
    output_file = "recorded_audio.wav"

    # Initialize PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(rate=16000, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=1024)

    # Initialize Voice Activity Detection (VAD)
    vad = webrtcvad.Vad()
    vad.set_mode(3)  # Aggressive mode

    def is_silence(frame, sample_rate):
        """Check if the frame is silent using VAD."""
        return not vad.is_speech(frame, sample_rate)

    def record_until_keyword():
        """Records audio until the keywords 'stop conversation' or 'end conversation' are detected."""
        print("Recording... Say 'stop conversation' or 'end conversation' to stop.")

        frames = []
        sample_rate = 16000
        frame_duration = 0.03  # 30ms
        frame_size = int(sample_rate * frame_duration)

        while True:
            data = stream.read(frame_size, exception_on_overflow=False)
            frames.append(data)

            # Save the audio every 2 seconds to check for keywords
            if len(frames) % int((sample_rate / frame_size) * 2) == 0:
                save_audio(frames)
                if check_for_stop_keyword(output_file):
                    break

        print("Stopping recording.")

    def save_audio(frames):
        """Saves recorded audio to a file."""
        audio_data = b"".join(frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        sf.write(output_file, audio_array, 16000)
        print(f"Audio saved to {output_file}")

    def check_for_stop_keyword(audio_file):
        """Transcribes the audio and checks for stop keywords."""
        try:
            print("Analyzing audio for stop keywords...")

            # Initialize Deepgram client
            deepgram = DeepgramClient(DEEPGRAM_API_KEY)

            # Read the audio file
            with open(audio_file, "rb") as file:
                buffer_data = file.read()

            payload: FileSource = {
                "buffer": buffer_data,
            }

            # Configure Deepgram options
            options = PrerecordedOptions(
                model="nova-3",
                smart_format=True
            )

            # Call the Deepgram API
            response = deepgram.listen.rest.v("1").transcribe_file(payload, options)

            # Extract the transcript
            transcript = response.results.channels[0].alternatives[0].transcript.lower()
            print(f"Transcription: {transcript}")

            # Check for stop keywords
            if "stop conversation" in transcript or "end conversation" in transcript:
                return True

        except Exception as e:
            print(f"Error during transcription: {e}")

        return False

    def transcribe_final_audio():
        """Transcribes the final audio and prints the text."""
        try:
            print("Sending final audio to Deepgram for transcription...")

            # Initialize Deepgram client
            deepgram = DeepgramClient(DEEPGRAM_API_KEY)

            # Read the audio file
            with open(output_file, "rb") as file:
                buffer_data = file.read()

            payload: FileSource = {
                "buffer": buffer_data,
            }

            # Configure Deepgram options
            options = PrerecordedOptions(
                model="nova-3",
                smart_format=True
            )

            # Call the Deepgram API
            response = deepgram.listen.rest.v("1").transcribe_file(payload, options)

            # Extract the transcript
            transcript = response.results.channels[0].alternatives[0].transcript
            insert_documents([transcript])

        except Exception as e:
            print(f"Error during final transcription: {e}")

    print("Starting immediate recording...")
    try:
        record_until_keyword()
        transcribe_final_audio()
    except KeyboardInterrupt:
        print("Recording interrupted by user.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
