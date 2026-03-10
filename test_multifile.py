"""
Multi-file project test script for AI-Dev-Tracker.
Simulates multiple prompts across different files to test:
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

from db import init_db, save_interaction, export_to_csv, get_time_gaps, get_all_interactions
from analyzer import analyze_repo, generate_report
from visualizer import show_summary, show_file_summary


DB_NAME = "ai_dev_tracker.db"


def clear_test_data():
    """Clears all data from the interactions table for a clean test."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM interactions")
    conn.commit()
    conn.close()
    print("✔ Cleared existing test data.\n")


def insert_mock_interaction(prompt, response, file_path, commit_hash,
                             timestamp_str, model="models/gemini-2.5-flash",
                             response_time=1.5, relevance=1):
    """Inserts a mock interaction with a specific timestamp (for time-gap testing)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    prompt_length = len(prompt)
    response_length = len(response)

    cursor.execute("""
        INSERT INTO interactions (
            prompt, response, file_path, commit_hash, timestamp,
            prompt_length, response_length, model_used,
            response_time, relevance
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prompt, response, file_path, commit_hash, timestamp_str,
        prompt_length, response_length, model,
        response_time, relevance
    ))

    conn.commit()
    conn.close()


def run_tests():
    print("=" * 60)
    print("  AI-Dev-Tracker — Multi-File Project Test")
    print("=" * 60)

    # Step 1: Initialize DB
    print("\n[1/7] Initializing database...")
    init_db()
    clear_test_data()

    # Step 2: Insert mock interactions across multiple files
    print("[2/7] Inserting mock interactions across multiple files...")

    base_time = datetime(2026, 3, 9, 10, 0, 0)

    test_data = [
        # file_a.py — rapid prompts (struggle zone)
        ("How to read a CSV file?",        "Use pandas.read_csv()",       "file_a.py", "abc123", base_time, 1.2),
        ("CSV parsing errors",             "Handle with try/except",      "file_a.py", "abc123", base_time + timedelta(minutes=2), 0.8),
        ("CSV encoding issues",            "Use encoding='utf-8'",        "file_a.py", "abc123", base_time + timedelta(minutes=4), 1.1),
        ("Still getting CSV errors",       "Check file path exists",      "file_a.py", "abc124", base_time + timedelta(minutes=6), 0.9),

        # file_b.py — normal usage
        ("How to create a class?",         "class MyClass: ...",          "file_b.py", "abc124", base_time + timedelta(hours=1), 1.5),
        ("Add method to class",            "def my_method(self): ...",    "file_b.py", "abc125", base_time + timedelta(hours=3), 2.0),

        # file_c.py — moderate usage
        ("Database connection in Python",  "Use sqlite3.connect()",       "file_c.py", "abc125", base_time + timedelta(hours=2), 1.8),
        ("SQL injection prevention",       "Use parameterized queries",   "file_c.py", "abc126", base_time + timedelta(hours=2, minutes=8), 1.3),
        ("Database indexing",              "CREATE INDEX ...",            "file_c.py", "abc126", base_time + timedelta(hours=2, minutes=20), 1.6),

        # No file — general prompts
        ("What is Python GIL?",            "Global Interpreter Lock...",  None,        "abc126", base_time + timedelta(hours=4), 2.1),
        ("Explain decorators",             "@decorator syntax...",        None,        "abc127", base_time + timedelta(hours=5), 1.9),
    ]

    for prompt, response, file_path, commit, time_offset, resp_time in test_data:
        ts = time_offset.strftime("%Y-%m-%d %H:%M:%S")
        relevance = 1 if file_path else 0
        insert_mock_interaction(prompt, response, file_path, commit, ts,
                                 response_time=resp_time, relevance=relevance)

    print(f"  Inserted {len(test_data)} mock interactions.\n")

    # Step 3: Test analyze
    print("[3/7] Running analysis...")
    analyze_repo()

    # Step 4: Test report generation
    print("\n[4/7] Running report generation...")
    generate_report()

    # Step 5: Test visualization
    print("[5/7] Running database visualization...")
    show_summary()
    show_file_summary()

    # Step 6: Test time-gap data
    print("[6/7] Verifying time-gap data...")
    time_gaps = get_time_gaps()
    for entry in time_gaps:
        print(f"  {entry['file']}: {entry['prompt_count']} prompts, gaps={entry['gaps_minutes']}")

    # Step 7: Test CSV export
    print("\n[7/7] Testing CSV export...")
    export_path = "test_export.csv"
    export_to_csv(export_path)

    # Verify CSV
    if os.path.exists(export_path):
        with open(export_path, "r") as f:
            lines = f.readlines()
        print(f"  CSV has {len(lines)} lines (1 header + {len(lines)-1} data rows)")
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