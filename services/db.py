import sqlite3
import json
import os

DB_PATH = "data/interviews.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            experience TEXT,
            resume_score INTEGER,
            asked_questions TEXT,
            answers TEXT,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_session(session_obj):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO interview_sessions 
        (user_id, role, experience, resume_score, asked_questions, answers, feedback) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session_obj.user_id,
        session_obj.role,
        session_obj.experience,
        session_obj.resume_score,
        json.dumps(session_obj.asked_questions),
        json.dumps(session_obj.answers),
        json.dumps(getattr(session_obj, "feedback", []))
    ))
    conn.commit()
    conn.close()
