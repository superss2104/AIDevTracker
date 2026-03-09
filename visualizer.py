from collections import defaultdict
from db import get_all_interactions


def show_summary():
    """Displays a tabular summary of all logged prompt interactions."""

    rows = get_all_interactions()

    if not rows:
        print("\n  No interactions found in the database.")
        return

    print("\n" + "=" * 100)
    print("  DATABASE VISUALIZATION — Prompt Log Summary")
    print("=" * 100)

    # Table header
    print(f"\n  {'ID':>4} │ {'Timestamp':>19} │ {'Model':>25} │ {'File':>20} │ {'Time(s)':>7} │ {'Prompt (truncated)'}")
    print("  " + "─" * 96)

    for row in rows:
        row_id = row[0]
        prompt = (row[1] or "")[:40].replace("\n", " ")
        file_path = row[3] or "—"
        timestamp = row[5] or "—"
        model = row[8] or "—"
        resp_time = row[9] or 0

        # Truncate long file paths
        if len(file_path) > 20:
            file_path = "..." + file_path[-17:]

        print(f"  {row_id:>4} │ {timestamp:>19} │ {model:>25} │ {file_path:>20} │ {resp_time:>7.2f} │ {prompt}")

    print("  " + "─" * 96)
    print(f"  Total: {len(rows)} interactions\n")


def show_file_summary():
    """Displays per-file prompt count as an ASCII bar chart."""

    rows = get_all_interactions()

    if not rows:
        print("\n  No interactions found.")
        return

    file_counts = defaultdict(int)
    no_file_count = 0

    for row in rows:
        file_path = row[3]
        if file_path:
            file_counts[file_path] += 1
        else:
            no_file_count += 1

    print("\n" + "=" * 60)
    print("  FILE USAGE SUMMARY")
    print("=" * 60)

    if file_counts:
        max_count = max(file_counts.values())
        scale = max(1, max_count // 30)

        for file, count in sorted(file_counts.items(), key=lambda x: -x[1]):
            bar = "█" * (count // scale) or "▏"
            print(f"  {file:30s} │ {bar} ({count})")

    if no_file_count > 0:
        print(f"\n  Prompts without file mapping: {no_file_count}")

    print("=" * 60 + "\n")
