import sys


def run(ask_fn, threshold=0.4):
    """Main CLI entry point. Parses commands and routes to handlers.

    Args:
        ask_fn    : The ask() function from main.py for handling 'ask' commands.
        threshold : Active relevance threshold (float 0.0–1.0), resolved in main.py
                    from .env or --threshold CLI flag.
    """

    # Lazy imports to avoid circular dependencies
    from analyzer import analyze_repo, generate_report
    from visualizer import show_summary, show_file_summary
    from db import export_to_csv

    # ── Strip --threshold from argv before command routing ────────────────
    # This ensures existing command parsing is completely unaffected.
    args = sys.argv[1:]
    if "--threshold" in args:
        idx = args.index("--threshold")
        # Remove both '--threshold' and its value
        args = [a for i, a in enumerate(args) if i != idx and i != idx + 1]
        sys.argv = [sys.argv[0]] + args

    # Command registry — add new commands here
    commands = {
        "ask":       {"args": True,  "help": 'ask "prompt" [file.py]'},
        "analyze":   {"args": False, "help": "analyze  [uses active threshold]"},
        "report":    {"args": False, "help": "report   [uses active threshold]"},
        "visualize": {"args": False, "help": "visualize"},
        "export":    {"args": True,  "help": "export [output.csv]"},
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
        ask_fn(prompt, file_path, threshold=threshold)

    elif command == "analyze":
        analyze_repo(threshold=threshold)

    elif command == "report":
        generate_report(threshold=threshold)

    elif command == "export":
        filepath = sys.argv[2] if len(sys.argv) > 2 else "ai_dev_tracker_export.csv"
        export_to_csv(filepath)

    elif command == "visualize":
        _handle_visualize()


def _handle_visualize():
    """Runs both visualization views."""
    from visualizer import show_summary, show_file_summary
    show_summary()
    show_file_summary()


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