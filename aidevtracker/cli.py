
import sys
import os

ACTIVE_SESSION_FILE = ".active_session"


def get_active_session_id():
    """Reads the active session ID from the .active_session file.
    Returns an int session_id or None if no session is active.
    """
    if not os.path.exists(ACTIVE_SESSION_FILE):
        return None
    try:
        with open(ACTIVE_SESSION_FILE, "r") as f:
            return int(f.read().strip())
    except (ValueError, OSError):
        return None


def set_active_session_id(session_id):
    """Writes the given session ID to the .active_session file."""
    with open(ACTIVE_SESSION_FILE, "w") as f:
        f.write(str(session_id))


def run(ask_fn, threshold=0.4):
    """Main CLI entry point. Parses commands and routes to handlers.

    Args:
        ask_fn    : The ask() function from main.py for handling 'ask' commands.
        threshold : Active relevance threshold (float 0.0–1.0), resolved in main.py
                    from .env or --threshold CLI flag.
    """

    # Lazy imports to avoid circular dependencies
    from .analyzer import analyze_repo, generate_report, analyze_file
    from .visualizer import show_summary, show_file_summary
    from .db import export_to_csv

    # ── Strip --threshold from argv before command routing ────────────────
    args = sys.argv[1:]
    if "--threshold" in args:
        idx = args.index("--threshold")
        args = [a for i, a in enumerate(args) if i != idx and i != idx + 1]
        sys.argv = [sys.argv[0]] + args

    session_id = get_active_session_id()

    # Command registry — add new commands here
    commands = {
        "ask":       {"args": True,  "help": 'ask "prompt" [file.py]'},
        "analyze":   {"args": True,  "help": "analyze [file.py]  [uses active threshold]"},
        "report":    {"args": False, "help": "report   [uses active threshold]"},
        "visualize": {"args": False, "help": "visualize"},
        "export":    {"args": True,  "help": "export [output.csv]"},
        "session":   {"args": True,  "help": "session <new|list|use|guard|summary> [args]"},
        "model":     {"args": True,  "help": "model <API_KEY> [--base-url URL] [--model MODEL]"},
    }

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        _print_usage(commands, threshold)
        sys.exit(0 if len(sys.argv) >= 2 else 1)

    command = sys.argv[1]

    if command not in commands:
        print(f"Unknown command: '{command}'")
        _print_usage(commands, threshold)
        sys.exit(1)

    if command == "ask":
        if len(sys.argv) < 3:
            print("Error: 'ask' requires a prompt argument.")
            print('Usage: python main.py ask "your prompt" [optional_file.py]')
            sys.exit(1)
        prompt = sys.argv[2]
        file_path = sys.argv[3] if len(sys.argv) > 3 else None
        ask_fn(prompt, file_path, session_id=session_id, threshold=threshold)

    elif command == "analyze":
        if len(sys.argv) > 2:
            analyze_file(sys.argv[2], session_id=session_id)
        else:
            analyze_repo(session_id=session_id, threshold=threshold)

    elif command == "report":
        generate_report(session_id=session_id, threshold=threshold)

    elif command == "export":
        filepath = sys.argv[2] if len(sys.argv) > 2 else "ai_dev_tracker_export.csv"
        export_to_csv(filepath, session_id=session_id)

    elif command == "visualize":
        _handle_visualize(session_id)

    elif command == "session":
        _handle_session()

    elif command == "model":
        _handle_model()

    else:
        print(f"Unknown command: '{command}'")


def _handle_visualize(session_id=None):
    """Runs both visualization views, scoped to the active session."""
    from .visualizer import show_summary, show_file_summary
    show_summary(session_id=session_id)
    show_file_summary(session_id=session_id)


def _handle_model():
    """Handles the 'model' command: updates LLM config in .env.
    - No args  → interactive provider selection (same as first-time setup)
    - With args → direct: python main.py model <KEY> [--base-url URL] [--model MODEL]
    """
    from .env_utils import update_env_key

    # ── Interactive mode (no extra args) ─────────────────────────────────
    if len(sys.argv) <= 2:
        providers = {
            "1": ("Gemini",  "https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-2.5-flash"),
            "2": ("OpenAI",  "https://api.openai.com/v1",                               "gpt-4o-mini"),
            "3": ("Groq",    "https://api.groq.com/openai/v1",                           "llama-3.3-70b-versatile"),
        }

        print("\nSelect your LLM provider:")
        for num, (name, _, _) in providers.items():
            print(f"  {num}. {name}")
        print("  4. Other (custom base URL)\n")

        choice = input("Enter choice (1-4): ").strip()

        if choice in providers:
            provider_name, base_url, default_model = providers[choice]
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
        print(f"✔ Configured {provider_name} ({model}) — saved to .env")
        return

    # ── Direct mode (args provided) ──────────────────────────────────────
    import argparse

    parser = argparse.ArgumentParser(prog="python main.py model", description="Update LLM configuration.")
    parser.add_argument("api_key", help="The API key for your LLM provider.")
    parser.add_argument("--base-url", help="The base URL (e.g. https://api.openai.com/v1).")
    parser.add_argument("--model", help="The model name (e.g. gpt-4o-mini).")

    args = parser.parse_args(sys.argv[2:])

    api_key = args.api_key.strip()
    if not api_key:
        print("Error: API key cannot be empty.")
        sys.exit(1)

    update_env_key("LLM_API_KEY", api_key)
    os.environ["LLM_API_KEY"] = api_key

    if args.base_url:
        update_env_key("LLM_BASE_URL", args.base_url)
        os.environ["LLM_BASE_URL"] = args.base_url

    if args.model:
        update_env_key("LLM_MODEL", args.model)
        os.environ["LLM_MODEL"] = args.model

    print("✔ LLM configuration updated successfully.")


def _handle_session():
    """Handles session sub-commands: new, list, use, guard, summary."""
    from .db import create_session, list_sessions, get_session_by_id, set_session_guard, get_session_summary

    if len(sys.argv) < 3:
        print("Usage: python main.py session <new|list|use|guard|summary> [args]")
        print("  session new  \"Project Name\" [--goal \"Goal text\"]   Create a new project session")
        print("  session list                                         List all sessions")
        print("  session use  <id>                                    Set the active session")
        print("  session guard <on|off>                               Toggle hard-block guard mode")
        print("  session summary                                      Show active session overview")
        sys.exit(1)

    sub = sys.argv[2]

    if sub == "new":
        if len(sys.argv) < 4:
            print("Error: 'session new' requires a project name.")
            print('Usage: python main.py session new "My Project" [--goal "Refactor CSV parser"]')
            sys.exit(1)
        project_name = sys.argv[3]

        # Parse optional --goal flag
        goal = ""
        if "--goal" in sys.argv:
            goal_idx = sys.argv.index("--goal")
            if goal_idx + 1 < len(sys.argv):
                goal = sys.argv[goal_idx + 1]
            else:
                print("Error: --goal requires a value.")
                sys.exit(1)

        # If no --goal flag, prompt interactively
        if not goal:
            try:
                goal = input("Session goal (optional, press Enter to skip): ").strip()
            except EOFError:
                goal = ""

        sid = create_session(project_name, goal=goal)
        if sid is None:
            print(f"Error: a session named \"{project_name}\" already exists.")
            print("Use 'session list' to see existing sessions, or 'session use <id>' to switch.")
            sys.exit(1)
        set_active_session_id(sid)
        print(f"\u2714 Created session #{sid} for project \"{project_name}\" (now active)")
        if goal:
            print(f"  Goal: {goal}")

    elif sub == "list":
        sessions = list_sessions()
        active = get_active_session_id()
        if not sessions:
            print("\n  No sessions found. Create one with: python main.py session new \"Project Name\"")
            return
        print(f"\n  {'ID':>4}  {'Project Name':25s}  {'Goal':30s}  {'Created At':19s}  Active")
        print("  " + "─" * 90)
        for row in sessions:
            sid, name, created = row[0], row[1], row[2]
            goal = row[3] if len(row) > 3 and row[3] else ""
            marker = " ◄" if sid == active else ""
            goal_display = (goal[:27] + "...") if len(goal) > 30 else goal
            print(f"  {sid:>4}  {name:25s}  {goal_display:30s}  {created:19s}  {marker}")
        print()

    elif sub == "use":
        if len(sys.argv) < 4:
            print("Error: 'session use' requires a session ID.")
            print("Usage: python main.py session use <id>")
            sys.exit(1)
        try:
            sid = int(sys.argv[3])
        except ValueError:
            print("Error: session ID must be an integer.")
            sys.exit(1)

        session = get_session_by_id(sid)
        if session is None:
            print(f"Error: session #{sid} not found.")
            sys.exit(1)

        set_active_session_id(sid)
        print(f"\u2714 Active session set to #{sid} (\"{session[1]}\")")

    elif sub == "guard":
        if len(sys.argv) < 4 or sys.argv[3] not in ("on", "off"):
            print("Usage: python main.py session guard <on|off>")
            sys.exit(1)

        active = get_active_session_id()
        if active is None:
            print("Error: no active session. Use 'session use <id>' first.")
            sys.exit(1)

        enabled = sys.argv[3] == "on"
        set_session_guard(active, enabled)
        state = "ENABLED" if enabled else "DISABLED"
        print(f"\u2714 Guard mode {state} for session #{active}.")
        if enabled:
            print("  Off-topic prompts will now be hard-blocked.")
        else:
            print("  Off-topic prompts will show a soft warning only.")

    elif sub == "summary":
        active = get_active_session_id()
        if active is None:
            print("Error: no active session. Use 'session use <id>' first.")
            sys.exit(1)

        data = get_session_summary(active)
        if data is None:
            print(f"Error: session #{active} not found in database.")
            sys.exit(1)

        guard_label = "\U0001f6ab ON (hard block)" if data["guard_mode"] else "\u26a0  OFF (soft warn)"
        print(f"\n{'=' * 55}")
        print(f"  SESSION SUMMARY  —  #{data['id']}: {data['project_name']}")
        print(f"{'=' * 55}")
        print(f"  Created    : {data['created_at']}")
        print(f"  Goal       : {data['goal'] or '(none set)'}")
        print(f"  Guard Mode : {guard_label}")
        print(f"\n  Interactions  : {data['total']} total  |  "
              f"{data['relevant']} relevant  |  {data['irrelevant']} off-topic")

        if data["files"]:
            print("\n  Files worked on:")
            for f in data["files"]:
                print(f"    \u2022 {f}")
        else:
            print("\n  Files worked on: (none)")

        if data["recent_prompts"]:
            print("\n  Recent prompts (newest first):")
            for i, (p, ts) in enumerate(data["recent_prompts"], 1):
                snippet = (p[:77] + "...") if len(p) > 80 else p
                print(f"    {i}. [{ts}] {snippet}")
        print(f"{'=' * 55}\n")

    else:
        print(f"Unknown session sub-command: '{sub}'")
        print("Available: new, list, use, guard, summary")
        sys.exit(1)


def _print_usage(commands, threshold=0.4):
    """Prints help text with all available commands and active threshold."""
    print("\nAI-Dev-Tracker — CLI Usage\n")
    print(f"  Active Relevance Threshold : {threshold}")
    print("  (Set via RELEVANCE_THRESHOLD in .env or override with --threshold <value>)\n")
    print("  python main.py [--threshold <0.0-1.0>] <command> [arguments]\n")
    print("Available commands:")
    for name, info in commands.items():
        print(f"  {info['help']:45s}")
    print()
    print("Examples:")
    print('  python main.py ask "How do I use async/await?" main.py')
    print('  python main.py --threshold 0.6 analyze')
    print('  python main.py --threshold 0.8 report')
    print()
