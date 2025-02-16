import os
import logging
from deepgram.utils import verboselogs
from deepgram import DeepgramClient, SpeakOptions
from pydub import AudioSegment
from pydub.playback import play
import time

# def play_audio(SPEAK_TEXT):
SPEAK_TEXT = {"text": "Studies of air bubbles trapped in amber show that the atmosphere of the Cretaceous may have had up to 35 per cent oxygen, compared to today's 21 per cent. For T. Rex this would feel like he was at the base camp of Everest. In such thin air dinosaurs would be too breathless to chase hapless tourists."}
filename = "test.wav"

try:
    # STEP 1 Create a Deepgram client using the API key from environment variables
    deepgram = DeepgramClient("81558636d0b88ce3ae9fd2e74706a50981c2133c")

    # STEP 2 Call the save method on the speak property
    options = SpeakOptions(model="aura-asteria-en")

    response = deepgram.speak.rest.v("1").save(filename, SPEAK_TEXT, options)
    print(response.to_json(indent=4))

    time.sleep(5)

    # STEP 3 Play the generated MP3 file
    if os.path.exists(filename):
        audio = AudioSegment.from_file("test.wav", format="wav")
        play(audio)
    else:
        print("Audio file not found!")

except Exception as e:
    print(f"Exception: {e}")