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


def run(ask_fn):
    """Main CLI entry point. Parses commands and routes to handlers.
    
    Args:
        ask_fn: The ask() function from main.py for handling 'ask' commands.
    """

    # Lazy imports to avoid circular dependencies
    from analyzer import analyze_repo, generate_report, analyze_file
    from visualizer import show_summary, show_file_summary
    from db import export_to_csv

    session_id = get_active_session_id()

    # Command registry — add new commands here
    commands = {
        "ask":       {"handler": _handle_ask,       "args": True,  "help": 'ask "prompt" [file.py]'},
        "analyze":   {"handler": None,              "args": True,  "help": "analyze [file.py]"},
        "report":    {"handler": lambda: generate_report(session_id=session_id),"args": False, "help": "report"},
        "visualize": {"handler": lambda: _handle_visualize(session_id), "args": False, "help": "visualize"},
        "export":    {"handler": None,               "args": True,  "help": "export [output.csv]"},
        "session":   {"handler": None,               "args": True,  "help": "session <new|list|use> [args]"},
    }

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        _print_usage(commands)
        sys.exit(0 if len(sys.argv) >= 2 else 1)

    command = sys.argv[1]

    if command not in commands:
        print(f"Unknown command: '{command}'")
        _print_usage(commands)
        sys.exit(1)

    if command == "ask":
        if len(sys.argv) < 3:
            print("Error: 'ask' requires a prompt argument.")
            print('Usage: python main.py ask "your prompt" [optional_file.py]')
            sys.exit(1)
        prompt = sys.argv[2]
        file_path = sys.argv[3] if len(sys.argv) > 3 else None
        ask_fn(prompt, file_path, session_id=session_id)

    elif command == "analyze":
        if len(sys.argv) > 2:
            analyze_file(sys.argv[2], session_id=session_id)
        else:
            analyze_repo(session_id=session_id)

    elif command == "export":
        filepath = sys.argv[2] if len(sys.argv) > 2 else "ai_dev_tracker_export.csv"
        export_to_csv(filepath, session_id=session_id)

    elif command == "visualize":
        _handle_visualize(session_id)

    elif command == "session":
        _handle_session()

    else:
        commands[command]["handler"]()


def _handle_ask(ask_fn, args):
    """Handled inline in run() for clarity."""
    pass


def _handle_visualize(session_id=None):
    """Runs both visualization views, scoped to the active session."""
    from visualizer import show_summary, show_file_summary
    show_summary(session_id=session_id)
    show_file_summary(session_id=session_id)


def _handle_session():
    """Handles session sub-commands: new, list, use."""
    from db import create_session, list_sessions, get_session_by_id

    if len(sys.argv) < 3:
        print("Usage: python main.py session <new|list|use> [args]")
        print("  session new  \"Project Name\"   Create a new project session")
        print("  session list                  List all sessions")
        print("  session use  <id>             Set the active session")
        sys.exit(1)

    sub = sys.argv[2]

    if sub == "new":
        if len(sys.argv) < 4:
            print("Error: 'session new' requires a project name.")
            print('Usage: python main.py session new "My Project"')
            sys.exit(1)
        project_name = sys.argv[3]
        sid = create_session(project_name)
        if sid is None:
            print(f"Error: a session named \"{project_name}\" already exists.")
            print("Use 'session list' to see existing sessions, or 'session use <id>' to switch.")
            sys.exit(1)
        set_active_session_id(sid)
        print(f"✔ Created session #{sid} for project \"{project_name}\" (now active)")

    elif sub == "list":
        sessions = list_sessions()
        active = get_active_session_id()
        if not sessions:
            print("\n  No sessions found. Create one with: python main.py session new \"Project Name\"")
            return
        print(f"\n  {'ID':>4}  {'Project Name':30s}  {'Created At':19s}  Active")
        print("  " + "─" * 65)
        for sid, name, created in sessions:
            marker = " ◀" if sid == active else ""
            print(f"  {sid:>4}  {name:30s}  {created:19s}  {marker}")
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
        print(f"✔ Active session set to #{sid} (\"{session[1]}\")")

    else:
        print(f"Unknown session sub-command: '{sub}'")
        print("Available: new, list, use")
        sys.exit(1)


def _print_usage(commands):
    """Prints help text with all available commands."""
    print("\nAI-Dev-Tracker — CLI Usage\n")
    print("  python main.py <command> [arguments]\n")
    print("Available commands:")
    for name, info in commands.items():
        print(f"  {info['help']:40s}")
    print()
