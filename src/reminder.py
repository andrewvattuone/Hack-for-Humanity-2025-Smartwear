from db_utils import query_documents, view_all_documents
from groq import Groq
from dotenv import load_dotenv
import os
from db_utils import insert_documents
from query_model import query_and_generate_response

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=api_key)

def create_reminder(command):
    prompt = f"""
    You are an assistent adding a reminder to a schedule. You need to slightly edit the inputted command, which will be inputted into a vector database afterward.
    Include all relevant information about the event, such as start time and what the event is about. Additionally, add the word "Scheduled event/reminder" before the rest of the entry in the vector database so that the
    reminder/event can be easily retrieved from the vector database at a later point in time"

    Event/reminder info:
    {command}

    Return the slightly edited string of the reminder/event:
    """

    # Query the LLaMA model
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-specdec",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    print(response.choices[0].message.content)

    insert_documents([response.choices[0].message.content])
    # print(f"🤖 Model Response:\n{response.choices[0].message.content}")
    # Return the generated response

def find_reminder(command):
    return query_and_generate_response("Scheduled event/reminder" + command)