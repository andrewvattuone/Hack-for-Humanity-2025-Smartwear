from groq import Groq
from dotenv import load_dotenv
import os
from query_model import query_and_generate_response
from record_conversation import record_conversation
# from play_audio import play_audio
from start_timer import start_timer
from stopwatch import start_stopwatch, end_stopwatch
from reminder import create_reminder, find_reminder

# Import the functions to be executed
# from some_module import record_audio, start_timer, start_stopwatch, schedule_event

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("Missing GROQ_API_KEY in .env file!")

# Initialize Groq client
groq_client = Groq(api_key=api_key)

def classify_command(command: str) -> str:
    """Classify the command and run the appropriate function."""
    prompt = f"""
    You are going to take the inputted command and run the correct function for it. If the inputted command
    doesn't match any of the listed functions, then process it as normal by passing the command directly to the model without choosing a function.
    If it's not asking anything about general knowledge, then say "command not recognized"

    List of Functions that can be run:
    query_model: if command is about summarizing a conversation or asking for specific information about a conversation (might not include the word
    conversation), then run this command
    record_audio: run if command says "start conversation" or "record conversation" then run this function
    start_timer: if command asks to start a timer for a set amount of time, run this function with the inputted time. Check the command for the inputted
    time duration and convert that to seconds, inside the corresponding if statement instead of running command, convert the inputted time into seconds
    (rounding to the nearest integer) and only input that number into the start_timer function
    start_stopwatch: if command asks to start stopwatch or asks to set a timer without a specified amount of time, run this function
    create_reminder: if the command asks to schedule an event, set a reminder, etc, then run this function and input the appropriate information about
    the event itself and the time it occurs
    find_reminder: if the command asks to find an event scheduled for a later time or asks to remind the user what events they may have coming up, then
    run this function with the inputted command
    play_audio: if any of the commands also say that audio should be played, then play the audio of those results in addition to running those commands

    Command: {command}
    
    Answer:
    """

    # Query the LLaMA model
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-specdec",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        model_response = response.choices[0].message.content.lower()

        # Determine which function to run based on model response
        if "query_model" in model_response:
            output = query_and_generate_response(command)
        elif "record_audio" in model_response:
            output = record_conversation()
        elif "start_timer" in model_response:
            start_timer(command)
        elif "start_stopwatch" in model_response:
            start_stopwatch()
        elif "end_stopwatch" in model_response:
            end_stopwatch()
        elif "create_reminder" in model_response:
            output = create_reminder(command)
        elif "find_reminder" in model_response:
            output = find_reminder(command)
        else:
            # Pass the command directly to the model without function execution
            general_response = groq_client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=[{"role": "user", "content": command}],
                temperature=0.7
            )
            output = general_response.choices[0].message.content

        # if "play_audio" in model_response:
        #     play_audio(output)
        
        return output

    except Exception as e:
        return f"Error processing command: {e}"

# Example usage
# if __name__ == "__main__":
#     user_input = input("Enter your command: ")
#     result = classify_command(user_input)
#     print(result)
    