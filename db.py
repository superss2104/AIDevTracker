
import sqlite3
from datetime import datetime

DB_NAME = "ai_dev_tracker.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ── Sessions table ──────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # ── Interactions table ──────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT,
            response TEXT,
            file_path TEXT,
            commit_hash TEXT,
            timestamp TEXT,
            prompt_length INTEGER,
            response_length INTEGER,
            model_used TEXT,
            response_time REAL,
            relevance FLOAT
        )
    """)

    # ── Migration: add session_id to existing databases ─────────
    try:
        cursor.execute("ALTER TABLE interactions ADD COLUMN session_id INTEGER")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════
#  Session helpers
# ═══════════════════════════════════════════════════════════════

def create_session(project_name):
    """Creates a new session and returns its id.
    Returns None if a session with the same name already exists.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check for duplicate name
    cursor.execute(
        "SELECT id FROM sessions WHERE project_name = ?", (project_name,)
    )
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return None  # duplicate

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO sessions (project_name, created_at) VALUES (?, ?)",
        (project_name, created_at),
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def list_sessions():
    """Returns all sessions as a list of (id, project_name, created_at)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, project_name, created_at FROM sessions ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_session_by_id(session_id):
    """Returns (id, project_name, created_at) or None."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, project_name, created_at FROM sessions WHERE id = ?",
        (session_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


# ═══════════════════════════════════════════════════════════════
#  Interaction CRUD (session-aware)
# ═══════════════════════════════════════════════════════════════

def save_interaction(prompt, response, file_path, commit_hash,
                     prompt_length, response_length,
                     model_used, response_time, relevance,
                     session_id=None):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO interactions (
            prompt, response, file_path, commit_hash, timestamp,
            prompt_length, response_length, model_used,
            response_time, relevance, session_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prompt, response, file_path, commit_hash, timestamp,
        prompt_length, response_length,
        model_used, response_time, relevance, session_id
    ))

    conn.commit()
    conn.close()

    print("✔ Interaction saved successfully.")


def get_recent_interactions(limit=5, session_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if session_id is not None:
        cursor.execute("""
            SELECT prompt, response FROM interactions
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (session_id, limit))
    else:
        cursor.execute("""
            SELECT prompt, response FROM interactions
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    rows.reverse()  # oldest first
    return rows  # list of (prompt, response)


def get_first_response_for_file(file_path, session_id=None):
    """Returns the first AI response ever logged for a given file.
    This serves as the base for relevance scoring of future prompts.
    Returns None if no prior interaction exists for this file.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if session_id is not None:
        cursor.execute("""
            SELECT response FROM interactions
            WHERE file_path = ? AND session_id = ?
            ORDER BY id ASC
            LIMIT 1
        """, (file_path, session_id))
    else:
        cursor.execute("""
            SELECT response FROM interactions
            WHERE file_path = ?
            ORDER BY id ASC
            LIMIT 1
        """, (file_path,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_first_prompt_for_file(file_path, session_id=None):
    """Returns the first AI prompt ever logged for a given file.
    This serves as the base for relevance scoring of future prompts.
    Returns None if no prior interaction exists for this file.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if session_id is not None:
        cursor.execute("""
            SELECT prompt FROM interactions
            WHERE file_path = ? AND session_id = ?
            ORDER BY id ASC
            LIMIT 1
        """, (file_path, session_id))
    else:
        cursor.execute("""
            SELECT prompt FROM interactions
            WHERE file_path = ?
            ORDER BY id ASC
            LIMIT 1
        """, (file_path,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_all_interactions(session_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if session_id is not None:
        cursor.execute(
            "SELECT * FROM interactions WHERE session_id = ?", (session_id,)
        )
    else:
        cursor.execute("SELECT * FROM interactions")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_time_gaps(session_id=None):
    """Returns time gaps between consecutive prompts per file.
    Result: list of dicts with file_path, timestamps, and gaps in minutes.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if session_id is not None:
        cursor.execute("""
            SELECT file_path, timestamp FROM interactions
            WHERE file_path IS NOT NULL AND file_path != ''
              AND session_id = ?
            ORDER BY file_path, timestamp
        """, (session_id,))
    else:
        cursor.execute("""
            SELECT file_path, timestamp FROM interactions
            WHERE file_path IS NOT NULL AND file_path != ''
            ORDER BY file_path, timestamp
        """)
    rows = cursor.fetchall()
    conn.close()

    from collections import defaultdict
    from datetime import datetime

    file_timestamps = defaultdict(list)
    for file_path, timestamp in rows:
        file_timestamps[file_path].append(timestamp)

    result = []
    for file_path, timestamps in file_timestamps.items():
        times = [datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t in timestamps]
        times.sort()
        gaps = []
        for i in range(1, len(times)):
            gap_minutes = (times[i] - times[i - 1]).total_seconds() / 60
            gaps.append(round(gap_minutes, 2))
        result.append({
            "file": file_path,
            "prompt_count": len(times),
            "timestamps": timestamps,
            "gaps_minutes": gaps
        })

    return result


def export_to_csv(filepath="ai_dev_tracker_export.csv", session_id=None):
    """Exports interactions to a CSV file, optionally filtered by session."""
    import csv

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if session_id is not None:
        cursor.execute(
            "SELECT * FROM interactions WHERE session_id = ?", (session_id,)
        )
    else:
        cursor.execute("SELECT * FROM interactions")
    rows = cursor.fetchall()

    columns = [
        "id", "prompt", "response", "file_path", "commit_hash",
        "timestamp", "prompt_length", "response_length",
        "model_used", "response_time", "relevance", "session_id"
    ]

    conn.close()

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)

    print(f"✔ Exported {len(rows)} interactions to {filepath}")
    return filepath
