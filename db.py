
import sqlite3
from datetime import datetime

DB_NAME = "ai_dev_tracker.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

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
            relevance INTEGER
        )
    """)

    conn.commit()
    conn.close()


def save_interaction(prompt, response, file_path, commit_hash,
                     prompt_length, response_length,
                     model_used, response_time, relevance):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO interactions (
            prompt, response, file_path, commit_hash, timestamp,
            prompt_length, response_length, model_used,
            response_time, relevance
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prompt, response, file_path, commit_hash, timestamp,
        prompt_length, response_length,
        model_used, response_time, relevance
    ))

    conn.commit()
    conn.close()

    print("✔ Interaction saved successfully.")