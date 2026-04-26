import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
import os
import re
from difflib import SequenceMatcher
from dotenv import load_dotenv
from .db import (
    init_db, save_interaction, get_first_response_for_file,
    get_session_goal, get_session_guard, get_first_prompt_for_file,
    get_recent_interactions,
)
from .ai_client import ask_gpt
from .git_utils import get_current_commit
from .cli import run

load_dotenv()

# ── Known providers (base_url, default_model) ────────────────────────────────
PROVIDERS = {
    "1": ("Gemini",  "https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-2.5-flash"),
    "2": ("OpenAI",  "https://api.openai.com/v1",                               "gpt-4o-mini"),
    "3": ("Groq",    "https://api.groq.com/openai/v1",                           "llama-3.3-70b-versatile"),
}


def _ensure_llm_config():
    """Prompt for LLM configuration if not already set in .env."""
    if len(sys.argv) >= 2 and sys.argv[1] == "model":
        return  # handled by the 'model' command

    from .env_utils import update_env_key, read_env_key

    # ── Backward compatibility: migrate old GEMINI_API_KEY ────────────────
    old_key = os.getenv("GEMINI_API_KEY", "").strip()
    current_key = os.getenv("LLM_API_KEY", "").strip()

    if old_key and old_key != "your_gemini_api_key_here" and not current_key:
        # Migrate silently
        update_env_key("LLM_API_KEY", old_key)
        update_env_key("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
        update_env_key("LLM_MODEL", "gemini-2.5-flash")
        os.environ["LLM_API_KEY"] = old_key
        os.environ["LLM_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
        os.environ["LLM_MODEL"] = "gemini-2.5-flash"
        print("✔ Migrated existing Gemini key to new LLM config.\n")
        return

    if current_key and current_key != "your_api_key_here":
        return  # already configured

    # ── Interactive provider selection ────────────────────────────────────
    print("No LLM configuration found. Let's set one up.\n")
    print("Select your LLM provider:")
    for num, (name, _, _) in PROVIDERS.items():
        print(f"  {num}. {name}")
    print("  4. Other (custom base URL)\n")

    choice = input("Enter choice (1-4): ").strip()

    if choice in PROVIDERS:
        provider_name, base_url, default_model = PROVIDERS[choice]
        model = input(f"Model name [{default_model}]: ").strip() or default_model
    elif choice == "4":
        provider_name = "Custom"
        base_url = input("Enter base URL: ").strip()
        if not base_url:
            print("Error: base URL cannot be empty.")
            sys.exit(1)
        model = input("Model name: ").strip()
        if not model:
            print("Error: model name cannot be empty.")
            sys.exit(1)
    else:
        print("Invalid choice.")
        sys.exit(1)

    api_key = input(f"Enter your {provider_name} API key: ").strip()
    if not api_key:
        print("Error: API key cannot be empty.")
        sys.exit(1)

    update_env_key("LLM_API_KEY", api_key)
    update_env_key("LLM_BASE_URL", base_url)
    update_env_key("LLM_MODEL", model)
    os.environ["LLM_API_KEY"] = api_key
    os.environ["LLM_BASE_URL"] = base_url
    os.environ["LLM_MODEL"] = model
    print(f"✔ Configured {provider_name} ({model}) — saved to .env\n")





# ── Resolve relevance threshold ──────────────────────────────────────────────
# Priority: CLI flag (--threshold x) > .env RELEVANCE_THRESHOLD > hardcoded 0.4
def _get_threshold():
    """Extract --threshold from sys.argv if present, else fall back to .env."""
    threshold = float(os.getenv("RELEVANCE_THRESHOLD", 0.4))
    args = sys.argv[1:]
    if "--threshold" in args:
        idx = args.index("--threshold")
        try:
            threshold = float(args[idx + 1])
        except (IndexError, ValueError):
            print("Warning: --threshold requires a numeric value (e.g. --threshold 0.6). Using default.")
    return threshold





# Common English stopwords to ignore during keyword comparison
STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "to", "of",
    "in", "for", "on", "with", "at", "by", "from", "as", "into", "about",
    "like", "through", "after", "over", "between", "out", "against", "during",
    "without", "before", "under", "around", "among", "and", "but", "or",
    "nor", "not", "so", "yet", "both", "either", "neither", "each", "every",
    "all", "any", "few", "more", "most", "other", "some", "such", "no",
    "only", "own", "same", "than", "too", "very", "just", "because", "if",
    "when", "while", "where", "how", "what", "which", "who", "whom", "this",
    "that", "these", "those", "it", "its", "i", "me", "my", "we", "our",
    "you", "your", "he", "him", "his", "she", "her", "they", "them", "their",
    "here", "there", "up", "down", "then", "once", "also", "s", "t", "re",
}


def _tokenize(text):
    """Extracts lowercase tokens, filtering out stopwords and short tokens."""
    tokens = re.findall(r'[a-zA-Z_]\w*', text.lower())
    return set(t for t in tokens if t not in STOPWORDS and len(t) > 1)


def _keyword_overlap(text_a, text_b):
    """Computes keyword overlap ratio between two texts.
    Returns (shared keywords) / (keywords in shorter text), giving a 0.0–1.0 score.
    """
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.0

    shared = tokens_a & tokens_b
    min_size = min(len(tokens_a), len(tokens_b))
    return len(shared) / min_size


def compute_relevance(response_text, file_path, session_id=None):
    """Hybrid relevance scoring against the first response for a file (the base).

    Uses two methods and takes the HIGHER score:
      1. SequenceMatcher — catches verbatim text/code reuse
      2. Keyword Overlap  — catches topical relevance (shared terms)

    - First prompt for a file → automatically scored 1.0 (it becomes the base).
    - No file_path → 0.0.
    """
    if not file_path:
        return 0.0

    base_response = get_first_response_for_file(file_path, session_id=session_id)

    if base_response is None:
        return 1.0

    seq_score = SequenceMatcher(None, response_text, base_response).ratio()
    kw_score = _keyword_overlap(response_text, base_response)

    final = max(seq_score, kw_score)
    return round(final, 4)


def ask(prompt, file_path=None, session_id=None, threshold=None):
    """Send a prompt to the AI, log interaction, and score relevance.

    Structured-session enforcement order (when session_id is set):
      1. Hard block  — if guard_mode is on AND relevance < threshold, reject.
      2. Soft warn   — if guard_mode is off AND relevance < threshold, ask y/N.
      3. Proceed     — send to AI with session_goal injected as system prompt.
    """
    if threshold is None:
        threshold = THRESHOLD

    # ── Fetch session context ─────────────────────────────────────────────────
    session_goal = ""
    guard_mode = False
    if session_id is not None:
        session_goal = get_session_goal(session_id)
        guard_mode = get_session_guard(session_id)

    # ── Pre-flight relevance check ────────────────────────────────────────────
    # Compare the new prompt against MULTIPLE context sources and take the MAX
    # score.  This prevents valid follow-ups ("What about java?") from being
    # blocked just because they don't share keywords with the very first prompt.
    #
    # Sources checked:
    #   1. First prompt for the same file  (topical anchor)
    #   2. Session goal                    (overall session scope)
    #   3. Most recent prompt + response   (conversational continuity)
    if session_id is not None and file_path:
        base_prompt = get_first_prompt_for_file(file_path, session_id=session_id)
        if base_prompt is not None:
            scores = [_keyword_overlap(prompt, base_prompt)]

            # Session goal comparison
            if session_goal:
                scores.append(_keyword_overlap(prompt, session_goal))

            # Most recent interaction comparison (prompt + response combined)
            recent = get_recent_interactions(limit=1, session_id=session_id)
            if recent:
                last_prompt, last_response = recent[-1]
                combined_context = f"{last_prompt} {last_response}"
                scores.append(_keyword_overlap(prompt, combined_context))

            pre_score = max(scores)

            if pre_score < threshold:
                if guard_mode:
                    print(f"\n🚫  GUARD MODE: Prompt blocked — off-topic for this session.")
                    if session_goal:
                        print(f"    Session goal : {session_goal}")
                    print(f"    Relevance    : {pre_score:.2f} (threshold: {threshold})")
                    print("    Use 'python main.py session guard off' to disable hard blocking.\n")
                    return
                else:
                    print(f"\n⚠   Off-topic warning: this query may not be relevant to the current session.")
                    if session_goal:
                        print(f"    Session goal : {session_goal}")
                    print(f"    Relevance    : {pre_score:.2f} (threshold: {threshold})")
                    try:
                        confirm = input("    Proceed anyway? [y/N]: ").strip().lower()
                    except EOFError:
                        confirm = "n"
                    if confirm != "y":
                        print("    Prompt cancelled.\n")
                        return
                    print()

    print(f"\nThinking...  [threshold={threshold}]\n")

    ai_result = ask_gpt(prompt, session_id=session_id, session_goal=session_goal)

    response_text = ai_result["text"]
    model_used = ai_result["model"]
    response_time = ai_result["response_time"]

    print("AI Response:\n")
    try:
        from rich.console import Console
        from rich.markdown import Markdown
        console = Console()
        console.print(Markdown(response_text))
    except ImportError:
        print(response_text)

    commit_hash = get_current_commit()

    prompt_length = len(prompt)
    response_length = len(response_text)

    relevance_score = compute_relevance(response_text, file_path, session_id=session_id)
    relevance = 1 if relevance_score >= threshold else 0

    print(f"\n\U0001f4ca Relevance Score: {relevance_score:.4f} ({'AI-contributed' if relevance else 'Not contributing'}) [threshold={threshold}]")

    save_interaction(
        prompt,
        response_text,
        file_path,
        commit_hash,
        prompt_length,
        response_length,
        model_used,
        response_time,
        relevance,
        session_id=session_id,
    )


def main():
    """Entry point for the installed 'aidt' console script."""
    load_dotenv()
    _ensure_llm_config()
    init_db()
    global THRESHOLD
    THRESHOLD = _get_threshold()
    run(ask, threshold=THRESHOLD)


if __name__ == "__main__":
    main()
