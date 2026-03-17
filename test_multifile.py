"""
Multi-file project test script for AI-Dev-Tracker.
Simulates multiple prompts across different files AND sessions to test:
  - Session creation and filtering
  - Interaction logging
  - Time-tracking and struggle detection
  - Analysis and report generation
  - Database visualization
  - CSV export

Uses direct DB inserts (mock) to avoid API calls.
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import (
    init_db, save_interaction, export_to_csv,
    get_time_gaps, get_all_interactions,
    create_session, list_sessions, get_session_by_id,
)
from analyzer import analyze_repo, generate_report
from visualizer import show_summary, show_file_summary


DB_NAME = "ai_dev_tracker.db"


def clear_test_data():
    """Clears all data from the interactions and sessions tables for a clean test."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM interactions")
    cursor.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()
    print("✔ Cleared existing test data.\n")


def insert_mock_interaction(prompt, response, file_path, commit_hash,
                             timestamp_str, model="models/gemini-2.5-flash",
                             response_time=1.5, relevance=1, session_id=None):
    """Inserts a mock interaction with a specific timestamp (for time-gap testing)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    prompt_length = len(prompt)
    response_length = len(response)

    cursor.execute("""
        INSERT INTO interactions (
            prompt, response, file_path, commit_hash, timestamp,
            prompt_length, response_length, model_used,
            response_time, relevance, session_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prompt, response, file_path, commit_hash, timestamp_str,
        prompt_length, response_length, model,
        response_time, relevance, session_id
    ))

    conn.commit()
    conn.close()


def run_tests():
    print("=" * 60)
    print("  AI-Dev-Tracker — Multi-File + Session Test")
    print("=" * 60)

    # Step 1: Initialize DB
    print("\n[1/9] Initializing database...")
    init_db()
    clear_test_data()

    # Step 2: Create sessions
    print("[2/9] Creating sessions...")
    sid_alpha = create_session("ProjectAlpha")
    sid_beta = create_session("ProjectBeta")
    print(f"  Created session #{sid_alpha} (ProjectAlpha)")
    print(f"  Created session #{sid_beta} (ProjectBeta)\n")

    # Verify sessions
    sessions = list_sessions()
    assert len(sessions) == 2, f"Expected 2 sessions, got {len(sessions)}"
    assert get_session_by_id(sid_alpha) is not None
    assert get_session_by_id(sid_beta) is not None
    print("  ✔ Session creation verified.\n")

    # Step 3: Insert mock interactions across multiple files AND sessions
    print("[3/9] Inserting mock interactions across files and sessions...")

    base_time = datetime(2026, 3, 9, 10, 0, 0)

    test_data = [
        # ── ProjectAlpha (sid_alpha): file_a.py — rapid prompts (struggle zone) ──
        ("How to read a CSV file?",        "Use pandas.read_csv()",       "file_a.py", "abc123", base_time,                              1.2, sid_alpha),
        ("CSV parsing errors",             "Handle with try/except",      "file_a.py", "abc123", base_time + timedelta(minutes=2),        0.8, sid_alpha),
        ("CSV encoding issues",            "Use encoding='utf-8'",        "file_a.py", "abc123", base_time + timedelta(minutes=4),        1.1, sid_alpha),
        ("Still getting CSV errors",       "Check file path exists",      "file_a.py", "abc124", base_time + timedelta(minutes=6),        0.9, sid_alpha),

        # ── ProjectAlpha (sid_alpha): file_b.py — normal usage ──
        ("How to create a class?",         "class MyClass: ...",          "file_b.py", "abc124", base_time + timedelta(hours=1),          1.5, sid_alpha),
        ("Add method to class",            "def my_method(self): ...",    "file_b.py", "abc125", base_time + timedelta(hours=3),          2.0, sid_alpha),

        # ── ProjectBeta (sid_beta): file_c.py — moderate usage ──
        ("Database connection in Python",  "Use sqlite3.connect()",       "file_c.py", "abc125", base_time + timedelta(hours=2),          1.8, sid_beta),
        ("SQL injection prevention",       "Use parameterized queries",   "file_c.py", "abc126", base_time + timedelta(hours=2, minutes=8), 1.3, sid_beta),
        ("Database indexing",              "CREATE INDEX ...",            "file_c.py", "abc126", base_time + timedelta(hours=2, minutes=20), 1.6, sid_beta),

        # ── ProjectBeta (sid_beta): no file — general prompts ──
        ("What is Python GIL?",            "Global Interpreter Lock...",  None,        "abc126", base_time + timedelta(hours=4),          2.1, sid_beta),
        ("Explain decorators",             "@decorator syntax...",        None,        "abc127", base_time + timedelta(hours=5),          1.9, sid_beta),
    ]

    for prompt, response, file_path, commit, time_offset, resp_time, sess in test_data:
        ts = time_offset.strftime("%Y-%m-%d %H:%M:%S")
        relevance = 1 if file_path else 0
        insert_mock_interaction(prompt, response, file_path, commit, ts,
                                 response_time=resp_time, relevance=relevance,
                                 session_id=sess)

    print(f"  Inserted {len(test_data)} mock interactions.\n")

    # Step 4: Verify session filtering
    print("[4/9] Verifying session-based filtering...")
    all_rows = get_all_interactions()
    alpha_rows = get_all_interactions(session_id=sid_alpha)
    beta_rows = get_all_interactions(session_id=sid_beta)
    print(f"  All interactions : {len(all_rows)}")
    print(f"  ProjectAlpha     : {len(alpha_rows)}")
    print(f"  ProjectBeta      : {len(beta_rows)}")
    assert len(all_rows) == 11, f"Expected 11 total, got {len(all_rows)}"
    assert len(alpha_rows) == 6, f"Expected 6 for Alpha, got {len(alpha_rows)}"
    assert len(beta_rows) == 5, f"Expected 5 for Beta, got {len(beta_rows)}"
    print("  ✔ Session filtering verified.\n")

    # Step 5: Test analyze (session-scoped)
    print("[5/9] Running analysis for ProjectAlpha...")
    analyze_repo(session_id=sid_alpha)

    print("\n[5/9] Running analysis for ProjectBeta...")
    analyze_repo(session_id=sid_beta)

    # Step 6: Test report generation (session-scoped)
    print("\n[6/9] Running report for ProjectAlpha...")
    generate_report(session_id=sid_alpha)

    # Step 7: Test visualization (session-scoped)
    print("[7/9] Running visualization for ProjectBeta...")
    show_summary(session_id=sid_beta)
    show_file_summary(session_id=sid_beta)

    # Step 8: Test time-gap data
    print("[8/9] Verifying time-gap data (ProjectAlpha)...")
    time_gaps = get_time_gaps(session_id=sid_alpha)
    for entry in time_gaps:
        print(f"  {entry['file']}: {entry['prompt_count']} prompts, gaps={entry['gaps_minutes']}")

    # Step 9: Test CSV export (session-scoped)
    print("\n[9/9] Testing CSV export (ProjectBeta)...")
    export_path = "test_export.csv"
    export_to_csv(export_path, session_id=sid_beta)

    # Verify CSV
    if os.path.exists(export_path):
        with open(export_path, "r") as f:
            lines = f.readlines()
        print(f"  CSV has {len(lines)} lines (1 header + {len(lines)-1} data rows)")
        assert len(lines) - 1 == 5, f"Expected 5 data rows for Beta, got {len(lines)-1}"
        os.remove(export_path)
        print(f"  ✔ Cleaned up {export_path}")
    else:
        print(f"  ✘ CSV file was not created!")

    # Final summary
    print("\n" + "=" * 60)
    print("  ✔ All tests completed successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_tests()
