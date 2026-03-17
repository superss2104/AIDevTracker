import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
import re
from difflib import SequenceMatcher
from db import init_db, save_interaction, get_first_response_for_file
from ai_client import ask_gpt
from git_utils import get_current_commit
from cli import run

RELEVANCE_THRESHOLD = 0.4

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

init_db()


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
    # Divide by the smaller set so short but relevant responses score high
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


def ask(prompt, file_path=None, session_id=None):

    print("\nThinking...\n")

    ai_result = ask_gpt(prompt, session_id=session_id)

    response_text = ai_result["text"]
    model_used = ai_result["model"]
    response_time = ai_result["response_time"]

    print("AI Response:\n")
    print(response_text)

    commit_hash = get_current_commit()

    prompt_length = len(prompt)
    response_length = len(response_text)

    relevance_score = compute_relevance(response_text, file_path, session_id=session_id)
    relevance = 1 if relevance_score >= RELEVANCE_THRESHOLD else 0

    print(f"\n📊 Relevance Score: {relevance_score:.4f} ({'AI-contributed' if relevance else 'Not contributing'})")

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


if __name__ == "__main__":
    run(ask)
