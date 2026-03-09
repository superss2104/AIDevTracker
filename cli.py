import sys


def run(ask_fn):
    """Main CLI entry point. Parses commands and routes to handlers.
    
    Args:
        ask_fn: The ask() function from main.py for handling 'ask' commands.
    """

    # Lazy imports to avoid circular dependencies
    from analyzer import analyze_repo, generate_report
    from visualizer import show_summary, show_file_summary
    from db import export_to_csv

    # Command registry — add new commands here
    commands = {
        "ask":       {"handler": _handle_ask,       "args": True,  "help": 'ask "prompt" [file.py]'},
        "analyze":   {"handler": lambda: analyze_repo(),   "args": False, "help": "analyze"},
        "report":    {"handler": lambda: generate_report(),"args": False, "help": "report"},
        "visualize": {"handler": lambda: _handle_visualize(), "args": False, "help": "visualize"},
        "export":    {"handler": None,               "args": True,  "help": "export [output.csv]"},
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
        ask_fn(prompt, file_path)

    elif command == "export":
        filepath = sys.argv[2] if len(sys.argv) > 2 else "ai_dev_tracker_export.csv"
        export_to_csv(filepath)

    elif command == "visualize":
        _handle_visualize()

    else:
        commands[command]["handler"]()


def _handle_ask(ask_fn, args):
    """Handled inline in run() for clarity."""
    pass


def _handle_visualize():
    """Runs both visualization views."""
    from visualizer import show_summary, show_file_summary
    show_summary()
    show_file_summary()


def _print_usage(commands):
    """Prints help text with all available commands."""
    print("\nAI-Dev-Tracker — CLI Usage\n")
    print("  python main.py <command> [arguments]\n")
    print("Available commands:")
    for name, info in commands.items():
        print(f"  {info['help']:40s}")
    print()