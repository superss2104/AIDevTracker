import os
import time
from google import genai
from dotenv import load_dotenv
from db import get_recent_interactions

load_dotenv()

MODEL_NAME = "models/gemini-2.5-flash"
MAX_HISTORY = 5

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def ask_gpt(prompt):

    start_time = time.time()

    # Build conversation history for context
    history = get_recent_interactions(MAX_HISTORY)
    contents = []
    for past_prompt, past_response in history:
        contents.append({"role": "user", "parts": [{"text": past_prompt}]})
        contents.append({"role": "model", "parts": [{"text": past_response}]})
    # Append current prompt
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
        )

        end_time = time.time()

        return {
            "text": response.text,
            "model": MODEL_NAME,
            "response_time": round(end_time - start_time, 2)
        }

    except Exception as e:
        return {
            "text": f"Error: {str(e)}",
            "model": MODEL_NAME,
            "response_time": 0
        }