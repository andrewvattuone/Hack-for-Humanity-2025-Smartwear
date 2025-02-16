# infinite_loop_listener.py

import speech_recognition as sr
import threading
from conversation_recorder import record_conversation

# Control flags
global_stop_flag = False
start_keywords = {"start recording", "record conversation", "begin recording"}


def listen_for_keywords():
    """Continuously listen for the start keyword to trigger recording."""
    global global_stop_flag

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("🎙️ Listening for the start keyword...")

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)

    while not global_stop_flag:
        with mic as source:
            print("👂 Listening...")
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio).lower()
            print(f"🗣️ Heard: {text}")

            if any(keyword in text for keyword in start_keywords):
                print("✅ Start keyword detected! Initiating recording...")
                recording_thread = threading.Thread(target=record_conversation)
                recording_thread.start()
                recording_thread.join()

        except sr.UnknownValueError:
            print("🤷 Couldn't understand the keyword.")
        except sr.RequestError as e:
            print(f"⚠️ Error with speech recognition: {e}")


if __name__ == "__main__":
    listen_for_keywords()

# from speech_to_text import record_conversation
# from pvrecorder import PvRecorder
# import wave
# import struct
# import time
# import google.generativeai as genai
# import os
# from dotenv import load_dotenv

# import speech_recognition as sr
# import threading

# START_KEYWORD = "record conversation"
# STOP_KEYWORD = "stop recording"

# # Global control flags
# is_recording = False
# stop_recording_flag = False

# def listen_for_keywords():
#     """Continuously listen for the start keyword unless recording."""
#     global is_recording

#     recognizer = sr.Recognizer()
#     mic = sr.Microphone()

#     print("🎙️ Listening for keyword...")

#     with mic as source:
#         recognizer.adjust_for_ambient_noise(source)

#     while True:
#         if not is_recording:
#             with mic as source:
#                 print("🛑 Listening for start keyword...")
#                 audio = recognizer.listen(source)

#             try:
#                 # Recognize speech
#                 text = recognizer.recognize_google(audio).lower()
#                 print(f"🗣️ Heard: {text}")

#                 if START_KEYWORD in text:
#                     print("✅ Keyword detected. Starting recording...")
#                     start_recording()
#             except sr.UnknownValueError:
#                 print("🤷 Couldn't understand the audio.")
#             except sr.RequestError as e:
#                 print(f"⚠️ Error with speech recognition: {e}")

# def start_recording():
#     """Starts the recording process."""
#     global is_recording, stop_recording_flag

#     is_recording = True
#     stop_recording_flag = False

#     # Run the recording in a separate thread
#     recording_thread = threading.Thread(target=record_conversation)
#     recording_thread.start()

# def record_conversation():
#     """Records a conversation until the stop keyword is heard."""
#     global is_recording, stop_recording_flag

#     device_index = -1  # Default microphone
#     frame_length = 512
#     output_file = "conversation_recording.wav"

#     # Initialize the recorder
#     recorder = PvRecorder(frame_length=frame_length, device_index=device_index)

#     try:
#         recorder.start()
#         print("🎙️ Recording conversation. Say 'stop recording' to end.")

#         frames = []
#         recognizer = sr.Recognizer()
#         mic = sr.Microphone()

#         # Start a listening thread for the stop keyword
#         stop_thread = threading.Thread(target=listen_for_stop_keyword)
#         stop_thread.start()

#         # Record while not stopping
#         while not stop_recording_flag:
#             frame = recorder.read()
#             frames.extend(frame)
#             time.sleep(0.1)  # Slight delay to reduce CPU usage

#         print("🛑 Stopping recording...")

#     finally:
#         recorder.stop()
#         recorder.delete()

#         # Save to WAV file
#         with wave.open(output_file, 'w') as f:
#             f.setparams((1, 2, 16000, 0, 'NONE', 'NONE'))
#             f.writeframes(struct.pack("h" * len(frames), *frames))

#         print(f"💾 Audio saved to {output_file}")
#         is_recording = False

# def listen_for_stop_keyword():
#     """Listens for the stop keyword during recording."""
#     global stop_recording_flag

#     recognizer = sr.Recognizer()
#     mic = sr.Microphone()

#     with mic as source:
#         recognizer.adjust_for_ambient_noise(source)

#     while not stop_recording_flag:
#         with mic as source:
#             print("🎙️ Listening for stop keyword...")
#             audio = recognizer.listen(source)

#         try:
#             text = recognizer.recognize_google(audio).lower()
#             print(f"🗣️ Heard during recording: {text}")

#             if STOP_KEYWORD in text:
#                 print("🛑 Stop keyword detected!")
#                 stop_recording_flag = True
#         except sr.UnknownValueError:
#             print("🤷 Couldn't understand the stop keyword.")
#         except sr.RequestError as e:
#             print(f"⚠️ Error with speech recognition: {e}")

# # Run the main listening loop
# if __name__ == "__main__":
#     listen_for_keywords()
