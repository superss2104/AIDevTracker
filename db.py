
import sqlite3
from datetime import datetime

DB_NAME = "history.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT,
            response TEXT,
            file_path TEXT,
            commit_hash TEXT,
            timestamp TEXT,
            relevance_score REAL,
            is_relevant INTEGER
        )
    """)

    conn.commit()
    conn.close()


def save_interaction(prompt, response, file_path, commit_hash):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO history (prompt, response, file_path, commit_hash, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (prompt, response, file_path, commit_hash, datetime.now()))

    conn.commit()
    conn.close()


def fetch_all():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM history")
    rows = c.fetchall()
    conn.close()
    return rows


def update_relevance(id, score, is_relevant):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        UPDATE history
        SET relevance_score = ?, is_relevant = ?
        WHERE id = ?
    """, (score, int(is_relevant), id))

    conn.commit()
    conn.close()