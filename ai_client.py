import os
import time
import difflib
from google import genai
from dotenv import load_dotenv
from db import get_recent_interactions

load_dotenv()

# Prevent "Both GOOGLE_API_KEY and GEMINI_API_KEY are set" warning
os.environ.pop("GOOGLE_API_KEY", None)

MODEL_NAME = "models/gemini-2.5-flash"
MAX_HISTORY = 5

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def ask_gpt(prompt, session_id=None):

    start_time = time.time()

    # Build conversation history for context (scoped to session)
    history = get_recent_interactions(MAX_HISTORY, session_id=session_id)
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


def evaluate_relevance(base_prompt, new_prompt, file_path=None):
    """Uses heuristics to determine if a new prompt is relevant to the 
    base prompt and the file context.
    Returns (score, is_relevant) where score is a 0.0-1.0 float
    and is_relevant is 1 if score >= 0.4, else 0.
    """
    
    # lowercase for more reliable matching
    base_prompt = str(base_prompt).lower()
    new_prompt = str(new_prompt).lower()
    
    score = 0.0
    
    # 1. Base String Overlap (0.0 to 1.0)
    score += difflib.SequenceMatcher(None, base_prompt, new_prompt).ratio()
    
    # 2. File Context Boost (+0.4)
    # If the prompt explicitly mentions the file name or 'file' or '.py'
    if file_path:
        filename = os.path.basename(file_path).lower()
        name_without_ext = os.path.splitext(filename)[0]
        if filename in new_prompt or name_without_ext in new_prompt or ".py" in new_prompt:
            score += 0.4
            
    # 3. Coding/Follow-up Intent Boost (+0.3)
    # Common words developers use to ask follow up questions about a file
    coding_keywords = {"better", "refactor", "add", "parameter", "code", 
                       "optimize", "fix", "improve", "update", "change", 
                       "remove", "explain", "error", "bug", "issue",
                       "logic", "function", "class", "method", "variable"}
    
    new_prompt_words = set(new_prompt.replace(".", "").replace("?", "").split())
    if len(coding_keywords.intersection(new_prompt_words)) > 0:
        score += 0.3
        
    # Cap score at 1.0
    score = min(1.0, score)
    
    is_relevant = 1 if score >= 0.4 else 0
    
    return score, is_relevant