import os
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "models/gemini-2.5-flash"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def ask_gpt(prompt):

    start_time = time.time()

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
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