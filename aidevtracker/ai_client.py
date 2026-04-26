import os
import time
import difflib
from openai import OpenAI
from dotenv import load_dotenv
from .db import get_recent_interactions

load_dotenv()

MAX_HISTORY = 5

# ── Cached client (recreated when key or base_url changes) ───────────────────
_client = None
_client_config = (None, None)


def _get_client():
    """Returns a cached OpenAI-compatible client, recreating only when config changes."""
    global _client, _client_config
    current_key = os.getenv("LLM_API_KEY", "")
    current_url = os.getenv("LLM_BASE_URL", "")
    config = (current_key, current_url)
    if _client is None or config != _client_config:
        _client = OpenAI(api_key=current_key, base_url=current_url)
        _client_config = config
    return _client


def _get_model():
    """Returns the active model name from the environment."""
    return os.getenv("LLM_MODEL", "gemini-2.5-flash")


def ask_gpt(prompt, session_id=None, session_goal=None):
    """Send a prompt to the AI and return the response dict.

    Args:
        prompt       : The user's query string.
        session_id   : Active session id (used to load conversation history).
        session_goal : Optional goal string — if set, a system message is
                       prepended to keep the AI focused on the session topic.
    """
    start_time = time.time()
    model = _get_model()

    # Build conversation history (OpenAI chat format)
    history = get_recent_interactions(MAX_HISTORY, session_id=session_id)
    messages = []

    # ── Inject system prompt when a session goal is defined ──────────────────
    if session_goal and session_goal.strip():
        messages.append({
            "role": "system",
            "content": (
                f"You are assisting a developer whose current session goal is: "
                f"\"{session_goal.strip()}\". "
                "Keep your answers focused on this goal. "
                "If a question appears unrelated to this goal, briefly note that "
                "it seems off-topic and, where possible, redirect your answer back "
                "to the session context."
            )
        })

    for past_prompt, past_response in history:
        messages.append({"role": "user", "content": past_prompt})
        messages.append({"role": "assistant", "content": past_response})
    # Append current prompt
    messages.append({"role": "user", "content": prompt})

    try:
        response = _get_client().chat.completions.create(
            model=model,
            messages=messages,
        )

        end_time = time.time()

        return {
            "text": response.choices[0].message.content,
            "model": model,
            "response_time": round(end_time - start_time, 2)
        }

    except Exception as e:
        return {
            "text": f"Error: {str(e)}",
            "model": model,
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