from collections import defaultdict
from datetime import datetime, timedelta
from db import get_all_interactions, get_time_gaps


def analyze_repo():

    rows = get_all_interactions()

    total = len(rows)
    relevant = sum(row[10] for row in rows)
    irrelevant = total - relevant

    file_usage = defaultdict(int)
    timestamps_by_file = defaultdict(list)

    for row in rows:
        file_path = row[3]
        timestamp = row[5]

        if file_path:
            file_usage[file_path] += 1
            timestamps_by_file[file_path].append(timestamp)

    print("\n===== AI ANALYSIS =====")
    print(f"Total Prompts: {total}")
    print(f"Relevant Prompts: {relevant}")
    print(f"Irrelevant Prompts: {irrelevant}")

    print("\nPrompts Per File:")
    for file, count in file_usage.items():
        print(f"  {file} → {count}")

    detect_struggles(timestamps_by_file)
    detect_time_struggles()


def detect_struggles(timestamps_by_file):

    print("\nPotential Struggle Zones:")
    found = False

    for file, timestamps in timestamps_by_file.items():

        times = [datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t in timestamps]
        times.sort()

        for i in range(len(times) - 2):
            if times[i + 2] - times[i] <= timedelta(minutes=30):
                print(f"  ⚠ High AI dependency detected on {file}")
                found = True
                break

    if not found:
        print("  No major struggle zones detected.")


def detect_time_struggles():
    """Analyzes time gaps between prompts to detect developer struggle.
    Flags files where prompts are fired rapidly (short gaps).
    """
    print("\nTime-Gap Struggle Analysis:")
    time_data = get_time_gaps()

    if not time_data:
        print("  No file-linked prompts found for time analysis.")
        return

    found_struggle = False
    for entry in time_data:
        file = entry["file"]
        gaps = entry["gaps_minutes"]
        count = entry["prompt_count"]

        if not gaps:
            continue

        avg_gap = sum(gaps) / len(gaps)
        min_gap = min(gaps)
        rapid_count = sum(1 for g in gaps if g < 5)

        print(f"\n  📄 {file}")
        print(f"     Prompts: {count} | Avg gap: {avg_gap:.1f} min | Min gap: {min_gap:.1f} min")

        if rapid_count >= 2:
            print(f"     ⚠ STRUGGLE DETECTED: {rapid_count} rapid prompts (< 5 min apart)")
            found_struggle = True
        elif avg_gap < 10:
            print(f"     ⚠ MODERATE STRUGGLE: Average gap under 10 minutes")
            found_struggle = True
        else:
            print(f"     ✔ Normal usage pattern")

    if not found_struggle:
        print("\n  No time-based struggle patterns detected.")


def generate_report():

    rows = get_all_interactions()

    total = len(rows)
    file_usage = defaultdict(int)
    model_usage = defaultdict(int)
    total_response_time = 0
    total_prompt_len = 0
    total_response_len = 0

    for row in rows:
        file_path = row[3]
        model = row[8]
        response_time = row[9] or 0
        prompt_len = row[6] or 0
        response_len = row[7] or 0

        if file_path:
            file_usage[file_path] += 1

        model_usage[model] += 1
        total_response_time += response_time
        total_prompt_len += prompt_len
        total_response_len += response_len

    # Header
    print("\n" + "=" * 50)
    print("       AI DEVELOPMENT REPORT")
    print("=" * 50)

    # Overall Statistics
    print("\n📊 Overall Statistics")
    print(f"  Total Prompts          : {total}")
    if total > 0:
        avg_response_time = total_response_time / total
        avg_prompt_len = total_prompt_len / total
        avg_response_len = total_response_len / total
        print(f"  Avg Response Time      : {avg_response_time:.2f}s")
        print(f"  Avg Prompt Length      : {avg_prompt_len:.0f} chars")
        print(f"  Avg Response Length    : {avg_response_len:.0f} chars")

    # File Breakdown
    print("\n📁 Per-File Breakdown")
    if file_usage:
        top_file = max(file_usage, key=file_usage.get)
        print(f"  Most AI-Assisted File  : {top_file} ({file_usage[top_file]} prompts)")
        print()
        for file, count in sorted(file_usage.items(), key=lambda x: -x[1]):
            bar = "█" * count
            print(f"  {file:30s} │ {bar} ({count})")
    else:
        print("  No file-linked prompts found.")

    # Model Usage
    print("\n🤖 Model Usage")
    for model, count in model_usage.items():
        print(f"  {model} → {count} prompts")

    # Struggle Summary
    print("\n⚠ Struggle Summary")
    time_data = get_time_gaps()
    struggle_files = []
    for entry in time_data:
        gaps = entry["gaps_minutes"]
        if gaps:
            rapid = sum(1 for g in gaps if g < 5)
            if rapid >= 2:
                struggle_files.append(entry["file"])

    if struggle_files:
        for f in struggle_files:
            print(f"  🔴 {f}")
    else:
        print("  No major struggle zones detected.")

    # Footer
    print("\n" + "=" * 50)
    print("       End of Report")
    print("=" * 50 + "\n")