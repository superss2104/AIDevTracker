import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta

DB_NAME = "ai_dev_tracker.db"


def fetch_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM interactions")
    rows = cursor.fetchall()
    conn.close()
    return rows


def analyze_repo():

    rows = fetch_data()

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
        print(f"{file} → {count}")

    detect_struggles(timestamps_by_file)


def detect_struggles(timestamps_by_file):

    print("\nPotential Struggle Zones:")
    found = False

    for file, timestamps in timestamps_by_file.items():

        times = [datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t in timestamps]
        times.sort()

        for i in range(len(times) - 2):
            if times[i + 2] - times[i] <= timedelta(minutes=30):
                print(f"⚠ High AI dependency detected on {file}")
                found = True
                break

    if not found:
        print("No major struggle zones detected.")


def generate_report():

    rows = fetch_data()

    total = len(rows)
    file_usage = defaultdict(int)
    model_usage = defaultdict(int)

    for row in rows:
        file_path = row[3]
        model = row[8]

        if file_path:
            file_usage[file_path] += 1

        model_usage[model] += 1

    print("\n===== AI DEVELOPMENT REPORT =====")
    print(f"Total Prompts: {total}")

    if file_usage:
        top_file = max(file_usage, key=file_usage.get)
        print(f"Most AI Assisted File: {top_file}")

    print("\nModel Usage:")
    for model, count in model_usage.items():
        print(f"{model} → {count}")

    print("=================================\n")