from collections import defaultdict
from datetime import datetime, timedelta
from db import get_all_interactions, get_time_gaps


# ─────────────────────────────────────────────
# Core Analysis Entry Points
# ─────────────────────────────────────────────

def analyze_repo(threshold=0.4):
    """Run full repository analysis including struggle detection.
    
    Args:
        threshold: Relevance threshold float (0.0 – 1.0). Interactions with
                   relevance score >= threshold are counted as relevant.
    """
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
    print(f"Active Relevance Threshold : {threshold}")
    print(f"Total Prompts              : {total}")
    print(f"Relevant Prompts           : {relevant}")
    print(f"Irrelevant Prompts         : {irrelevant}")

    print("\nPrompts Per File:")
    for file, count in file_usage.items():
        print(f"  {file} → {count}")

    # Struggle detection — all methods
    detect_struggles(timestamps_by_file)
    detect_time_struggles()


def generate_report(threshold=0.4):
    """Generate a detailed AI contribution report.
    
    Args:
        threshold: Relevance threshold float used for display context.
    """
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
    print(f"\n⚙  Active Relevance Threshold : {threshold}")

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

    # Full Struggle Summary
    print("\n⚠ Struggle Summary")
    time_data = get_time_gaps()
    rapid_files = []
    sustained_files = []
    escalation_files = []

    for entry in time_data:
        gaps = entry["gaps_minutes"]
        timestamps = entry["timestamps"]
        file = entry["file"]

        if not gaps:
            continue

        # Rapid-prompt struggle (existing): 2+ gaps < 5 min
        rapid = sum(1 for g in gaps if g < 5)
        if rapid >= 2:
            rapid_files.append((file, rapid))

        # Sustained struggle (new): 3+ prompts within a 30-min rolling window
        if _has_sustained_struggle(timestamps, window_minutes=30, min_prompts=3):
            sustained_files.append(file)

        # Escalation struggle (new): Prompt frequency accelerating over time
        if _has_escalating_frequency(gaps):
            escalation_files.append(file)

    any_struggle = rapid_files or sustained_files or escalation_files

    if rapid_files:
        print("\n  🔴 Rapid-Prompt Struggle (< 5 min between prompts):")
        for f, count in rapid_files:
            print(f"     {f}  [{count} rapid prompts]")

    if sustained_files:
        print("\n  🔶 Sustained Struggle (3+ prompts within 30-min window):")
        for f in sustained_files:
            print(f"     {f}")

    if escalation_files:
        print("\n  📈 Escalating Dependency (prompt frequency increasing rapidly):")
        for f in escalation_files:
            print(f"     {f}")

    if not any_struggle:
        print("  No major struggle zones detected.")

    # Footer
    print("\n" + "=" * 50)
    print("       End of Report")
    print("=" * 50 + "\n")


# ─────────────────────────────────────────────
# Struggle Detection Functions
# ─────────────────────────────────────────────

def detect_struggles(timestamps_by_file):
    """Legacy per-file struggle detector: 3 prompts within any 30-min window."""
    print("\nPotential Struggle Zones:")
    found = False

    for file, timestamps in timestamps_by_file.items():
        if _has_sustained_struggle(timestamps, window_minutes=30, min_prompts=3):
            print(f"  ⚠ High AI dependency detected on {file}")
            found = True

    if not found:
        print("  No major struggle zones detected.")


def detect_time_struggles():
    """Analyzes time gaps between prompts to detect developer struggle.

    Detection methods applied per file:
      1. Rapid-prompt  : 2+ consecutive gaps < 5 minutes apart          [existing]
      2. Moderate avg  : Average gap < 10 minutes                        [existing]
      3. Sustained     : 3+ prompts occurring within any 30-min window   [NEW]
      4. Escalating    : Prompt frequency accelerating over time         [NEW]
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
        timestamps = entry["timestamps"]
        count = entry["prompt_count"]

        if not gaps:
            continue

        avg_gap = sum(gaps) / len(gaps)
        min_gap = min(gaps)
        rapid_count = sum(1 for g in gaps if g < 5)

        print(f"\n  📄 {file}")
        print(f"     Prompts: {count} | Avg gap: {avg_gap:.1f} min | Min gap: {min_gap:.1f} min")

        flags = []

        # ── Existing: Rapid-prompt detection ──────────────────────────────
        if rapid_count >= 2:
            flags.append(f"     ⚠  STRUGGLE DETECTED : {rapid_count} rapid prompts (< 5 min apart)")
        elif avg_gap < 10:
            flags.append(f"     ⚠  MODERATE STRUGGLE  : Average gap under 10 minutes")

        # ── NEW: Sustained 30-minute window detection ──────────────────────
        if _has_sustained_struggle(timestamps, window_minutes=30, min_prompts=3):
            flags.append(
                "     🔶 SUSTAINED STRUGGLE : 3+ prompts fired within a 30-min session"
            )

        # ── NEW: Escalating frequency detection ───────────────────────────
        if _has_escalating_frequency(gaps):
            flags.append(
                "     📈 ESCALATING DEPS    : Prompts are getting progressively closer together"
            )

        # ── NEW: Long-session detection (total active span > 2 hours) ─────
        if _has_long_session(timestamps, threshold_hours=2):
            flags.append(
                "     🕐 LONG SESSION       : Continuous AI usage detected over 2+ hours on this file"
            )

        if flags:
            for f in flags:
                print(f)
            found_struggle = True
        else:
            print("     ✔ Normal usage pattern")

    if not found_struggle:
        print("\n  No time-based struggle patterns detected.")


# ─────────────────────────────────────────────
# Private Helpers for Struggle Logic
# ─────────────────────────────────────────────

def _has_sustained_struggle(timestamps, window_minutes=30, min_prompts=3):
    """Return True if `min_prompts` or more prompts fall within any rolling
    window of `window_minutes` minutes.

    Args:
        timestamps : List of timestamp strings ("%Y-%m-%d %H:%M:%S").
        window_minutes : Size of the rolling window in minutes.
        min_prompts    : Minimum prompts required within the window to flag.

    Returns:
        bool
    """
    if len(timestamps) < min_prompts:
        return False

    times = sorted(
        datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t in timestamps
    )
    window = timedelta(minutes=window_minutes)

    # Sliding window: for each anchor point, count how many timestamps
    # fall within [anchor, anchor + window_minutes].
    for i in range(len(times)):
        count_in_window = sum(
            1 for t in times[i:] if t - times[i] <= window
        )
        if count_in_window >= min_prompts:
            return True

    return False


def _has_escalating_frequency(gaps):
    """Return True if prompt gaps are consistently shrinking (frequency rising).
    
    Requires at least 3 gaps. A sequence is considered escalating if each
    consecutive gap is shorter than the previous one for more than 60% of the
    transitions.

    Args:
        gaps: List of floats (minutes between consecutive prompts).

    Returns:
        bool
    """
    if len(gaps) < 3:
        return False

    shrinking = sum(
        1 for i in range(1, len(gaps)) if gaps[i] < gaps[i - 1]
    )
    ratio = shrinking / (len(gaps) - 1)
    return ratio >= 0.6


def _has_long_session(timestamps, threshold_hours=2):
    """Return True if the total span of AI usage on a file exceeds threshold_hours.

    Args:
        timestamps      : List of timestamp strings.
        threshold_hours : Hours threshold for a 'long session'.

    Returns:
        bool
    """
    if len(timestamps) < 2:
        return False

    times = sorted(
        datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t in timestamps
    )
    span = times[-1] - times[0]
    return span >= timedelta(hours=threshold_hours)