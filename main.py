import sys
import os
from dotenv import load_dotenv

from db import init_db, save_interaction
from ai_client import ask_gpt
from git_utils import get_current_commit
from cli import run

load_dotenv()

init_db()

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


THRESHOLD = _get_threshold()


def ask(prompt, file_path=None, threshold=None):
    """Send a prompt to the AI, log interaction, and score relevance.

    Args:
        prompt    : The user's prompt text.
        file_path : Optional file that the prompt relates to.
        threshold : Relevance threshold. Prompts are marked relevant (1)
                    when the file_path is provided AND the response
                    is substantive (len > threshold * 100 chars as a simple
                    proxy until a full similarity scorer is integrated).
    """
    if threshold is None:
        threshold = THRESHOLD

    print(f"\nThinking...  [threshold={threshold}]\n")

    ai_result = ask_gpt(prompt)

    response_text = ai_result["text"]
    model_used = ai_result["model"]
    response_time = ai_result["response_time"]

    print("AI Response:\n")
    print(response_text)

    commit_hash = get_current_commit()

    prompt_length = len(prompt)
    response_length = len(response_text)

    # Relevance scoring:
    # A response is considered relevant if:
    #   - A file_path was provided (file-linked prompt), AND
    #   - The response is substantive (length > threshold * 500 chars proxy)
    if file_path:
        relevance = 1 if response_length >= threshold * 500 else 0
    else:
        relevance = 0

    print(f"\n✔ Relevance score: {'Relevant' if relevance else 'Not relevant'} (threshold={threshold})")

    save_interaction(
        prompt,
        response_text,
        file_path,
        commit_hash,
        prompt_length,
        response_length,
        model_used,
        response_time,
        relevance
    )


if __name__ == "__main__":
    run(ask, threshold=THRESHOLD)