from db_utils import query_documents, view_all_documents
from groq import Groq
from dotenv import load_dotenv
import os

def start_timer(command):
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    groq_client = Groq(api_key=api_key)

    prompt = f"""
    You are calculating the amount of time a timer should run for in seconds. Scan the message for the inputted time duration,
    and calculate the amount of seconds the timer should run for. Round to the nearest integer. Your output should be ONLY ONE NUMBER (the number
    of seconds the timer should run for) AND NOTHING ELSE - NO EXTRA TEXT AT ALL
    "

    Original command: {command}

    Calculate the integer number of seconds the timer should run for - just return the number, nothing else:
    """

    # Query the LLaMA model
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-specdec",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    seconds = response.choices[0].message.content
    print(seconds)
    return seconds