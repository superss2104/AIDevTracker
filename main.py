import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
from db import init_db, save_interaction, get_first_prompt_for_file
from ai_client import ask_gpt, evaluate_relevance
from git_utils import get_current_commit
from analyzer import analyze_repo, generate_report, analyze_file

init_db()


def ask(prompt, file_path=None):

    print("\nThinking...\n")

    ai_result = ask_gpt(prompt)

    response_text = ai_result["text"]
    model_used = ai_result["model"]
    response_time = ai_result["response_time"]

    print("AI Response:\n")
    print(response_text)

    commit_hash = get_current_commit()

    prompt_length = len(prompt)
    response_length = len(response_text)

    relevance = 0
    if file_path:
        base_prompt = get_first_prompt_for_file(file_path)
        if base_prompt is None:
            relevance = 1 # first prompt is always relevant
            print(f"\n[Relevance Score: 1.00 (Base Prompt) -> Relevant]")
        else:
            score, relevance = evaluate_relevance(base_prompt, prompt, file_path)
            rel_str = "Relevant" if relevance == 1 else "Irrelevant"
            print(f"\n[Relevance Score: {score:.2f} (Threshold: 0.4) -> {rel_str}]")

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

    if len(sys.argv) < 2:
        print("""
Usage:
  python main.py ask "prompt" optional_file.py
  python main.py analyze [optional_file.py]
  python main.py report
        """)
        sys.exit(1)

    command = sys.argv[1]

    if command == "ask":
        prompt = sys.argv[2]
        file_path = sys.argv[3] if len(sys.argv) > 3 else None
        ask(prompt, file_path)

    elif command == "analyze":
        if len(sys.argv) > 2:
            from analyzer import analyze_file
            analyze_file(sys.argv[2])
        else:
            analyze_repo()

    elif command == "report":
        generate_report()

    else:
        print("Unknown command.")