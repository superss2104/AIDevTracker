from collections import defaultdict
from datetime import datetime, timedelta
import ast
import os
from db import get_all_interactions, get_time_gaps, get_session_by_id


def analyze_repo(session_id=None):

    rows = get_all_interactions(session_id=session_id)

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
    if session_id is not None:
        session = get_session_by_id(session_id)
        if session:
            print(f"  Session: #{session[0]} — {session[1]}")
    print(f"Total Prompts: {total}")
    print(f"Relevant Prompts: {relevant}")
    print(f"Irrelevant Prompts: {irrelevant}")

    print("\nPrompts Per File:")
    for file, count in file_usage.items():
        print(f"  {file} → {count}")

    detect_struggles(timestamps_by_file)
    detect_time_struggles(session_id=session_id)


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


def detect_time_struggles(session_id=None):
    """Analyzes time gaps between prompts to detect developer struggle.
    Flags files where prompts are fired rapidly (short gaps).
    """
    print("\nTime-Gap Struggle Analysis:")
    time_data = get_time_gaps(session_id=session_id)

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


def generate_report(session_id=None):

    rows = get_all_interactions(session_id=session_id)

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

    if session_id is not None:
        session = get_session_by_id(session_id)
        if session:
            print(f"  Session: #{session[0]} — {session[1]}")

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
    time_data = get_time_gaps(session_id=session_id)
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


def get_dependencies(file_path):
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    deps = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                deps.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                deps.add(node.module.split('.')[0])

    # Filter to only local matching Python files/packages
    local_deps = []
    base_dir = os.path.dirname(os.path.abspath(file_path)) or "."
    for dep in deps:
        if os.path.exists(os.path.join(base_dir, f"{dep}.py")) or os.path.isdir(os.path.join(base_dir, dep)):
            local_deps.append(dep)

    return sorted(local_deps)


def analyze_file(target_file, session_id=None):
    rows = get_all_interactions(session_id=session_id)

    # Filter interactions for the specific file
    file_rows = [row for row in rows if row[3] == target_file]

    total = len(file_rows)
    relevant = sum(row[10] for row in file_rows if row[10] is not None) if total > 0 else 0
    irrelevant = total - relevant

    print(f"\n===== AI ANALYSIS FOR: {target_file} =====")
    if session_id is not None:
        session = get_session_by_id(session_id)
        if session:
            print(f"  Session: #{session[0]} — {session[1]}")
    print(f"Total Prompts: {total}")
    print(f"Relevant Prompts: {relevant}")
    print(f"Irrelevant Prompts: {irrelevant}")

    # Dependencies
    deps = get_dependencies(target_file)
    if deps:
        print("\nLocal Dependencies:")
        for dep in deps:
            print(f"  - {dep}")
    else:
        print("\nLocal Dependencies: None")

    # Struggle Factor
    if total > 0:
        time_data = get_time_gaps(session_id=session_id)
        gaps = []
        for entry in time_data:
            if entry["file"] == target_file:
                gaps = entry["gaps_minutes"]
                break

        score, category, details = calculate_struggle_score(gaps, irrelevant, total)

        print(f"\nStruggle Score: {score}/100 ({category})")
        if details:
            for detail in details:
                print(f"  - {detail}")
        else:
            print("  - Output structure behaves normally.")

    # Footer
    print("\n" + "=" * 50)
    print("       End of Report")
    print("=" * 50 + "\n")


def calculate_struggle_score(gaps, irrelevant_count, total_prompts):
    """Calculates a 0-100 struggle score and assigns a severity category."""
    score = 0
    details = []

    # 1. Volume (max 40)
    if total_prompts > 1:
        volume_penalty = min(total_prompts * 5, 40)
        score += volume_penalty
        if volume_penalty >= 20:
            details.append(f"High prompt volume ({total_prompts} questions)")

    # 2. Irrelevance (max 20)
    if irrelevant_count > 0:
        irrel_penalty = min(irrelevant_count * 10, 20)
        score += irrel_penalty
        details.append(f"Off-topic/Irrelevant prompts detected ({irrelevant_count})")

    # 3. Time gaps
    if gaps:
        rapid_count = sum(1 for g in gaps if g < 3)
        prolonged_count = sum(1 for g in gaps if 5 <= g <= 30)

        # Rapid fire (max 20)
        if rapid_count > 0:
            rapid_penalty = min(rapid_count * 10, 20)
            score += rapid_penalty
            details.append(f"Frustrated/Rapid-fire prompts detected ({rapid_count} under 3 mins)")

        # Prolonged debugger (max 20)
        if prolonged_count > 0:
            prolonged_penalty = min(prolonged_count * 5, 20)
            score += prolonged_penalty
            details.append(f"Prolonged debugging sessions detected ({prolonged_count} gaps of 5-30 mins)")

    score = min(score, 100)
    score = max(score, 0)

    if score >= 75:
        category = "CRITICAL"
    elif score >= 50:
        category = "HIGH"
    elif score >= 25:
        category = "MODERATE"
    else:
        category = "LOW"

    return score, category, details
