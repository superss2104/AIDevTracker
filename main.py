import sys
from db import init_db, save_interaction
from ai_client import ask_gpt
from git_utils import get_current_commit
from analyzer import analyze_repo, generate_report

init_db()


def ask(prompt, file_path=None):
    print("\nThinking...\n")

    response = ask_gpt(prompt)

    print("AI Response:\n")
    print(response)

    commit_hash = get_current_commit()

    save_interaction(prompt, response, file_path, commit_hash)

    print("\n✔ Interaction saved successfully.\n")


def analyze():
    print("\nRunning analysis...\n")
    analyze_repo()
    generate_report()


def status():
    print("\nAI Dev Tracker Status:")
    print("----------------------")
    print("Database initialized.")
    print("Git linked.")
    print("Ready to track AI development.\n")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python main.py ask \"your prompt\" optional_file.py")
        print("  python main.py analyze")
        print("  python main.py status\n")
        sys.exit(1)

    command = sys.argv[1]

    if command == "ask":

        if len(sys.argv) < 3:
            print("Error: Please provide a prompt.")
            sys.exit(1)

        prompt = sys.argv[2]
        file_path = sys.argv[3] if len(sys.argv) > 3 else None

        ask(prompt, file_path)

    elif command == "analyze":
        analyze()

    elif command == "status":
        status()

    else:
        print("Unknown command.")