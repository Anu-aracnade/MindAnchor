# database.py
# Updated DB helper for MindAnchor: supports user profiles, focus sessions, and AI logs

import os
import sqlite3

DB_PATH = os.path.join("data", "mindanchor_ai.db")

def init_db():
    """Initialize DB tables if not present."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT,
            age INTEGER,
            gender TEXT,
            interest TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Focus sessions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_name TEXT,
            duration_sec INTEGER,
            distractions INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            start_time TEXT,
            end_time TEXT,
            ai_comment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Simple AI logs for optional training
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id INTEGER,
            focus_score REAL,
            recommended_duration INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    """)

    conn.commit()
    conn.close()

def save_user(name, country, age, gender, interest):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (name, country, age, gender, interest)
        VALUES (?, ?, ?, ?, ?)
    """, (name, country, age, gender, interest))
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    return uid

def save_session(user_id, session_name, duration_sec, distractions, completed, ai_comment=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sessions (user_id, session_name, duration_sec, distractions, completed, ai_comment)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, session_name, duration_sec, distractions, int(bool(completed)), ai_comment))
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid

def save_ai_log(user_id, session_id, focus_score, recommended_duration):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ai_logs (user_id, session_id, focus_score, recommended_duration)
        VALUES (?, ?, ?, ?)
    """, (user_id, session_id, focus_score, recommended_duration))
    conn.commit()
    conn.close()

def fetch_sessions_for_user(user_id, limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, session_name, duration_sec, distractions, completed, created_at, ai_comment
        FROM sessions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    print("✅ MindAnchor AI database initialized.")