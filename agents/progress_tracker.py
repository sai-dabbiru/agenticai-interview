import sqlite3
import statistics
import json
from agents.domain_classifier import classify_role_to_domain
from services.db import DB_PATH

def get_user_and_peer_scores(user_id: str, role: str):
    domain = classify_role_to_domain(role)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, feedback
        FROM interview_sessions
    """)
    rows = cursor.fetchall()
    conn.close()

    all_scores = []
    user_scores = []

    for uid, feedback_json in rows:
        try:
            feedback = json.loads(feedback_json)
            total = sum(item.get("score", 0) for item in feedback)
            count = len(feedback)
            avg = total / count if count else 0
        except:
            avg = 0

        if avg > 0:
            all_scores.append((uid, avg))
            if uid == user_id:
                user_scores.append(avg)

    return user_scores, all_scores

def generate_progress_feedback(user_id: str, role: str):
    user_scores, all_scores = get_user_and_peer_scores(user_id, role)

    if not user_scores:
        return "No prior interview sessions found."

    current_avg = user_scores[-1]
    previous_avg = user_scores[-2] if len(user_scores) > 1 else None

    max_per_question = 5
    num_questions = 3  # ideally fetch from session or feedback length
    max_total = max_per_question * num_questions
    total_score = round(current_avg * num_questions, 2)
    percentage_score = round((total_score / max_total) * 100, 2)

    feedback = f"Your current score is {total_score}/{max_total} ({percentage_score}%).\n\n"

    # Improvement from previous
    if previous_avg:
        previous_total = round(previous_avg * num_questions, 2)
        previous_percent = (previous_total / max_total) * 100
        delta_percent = round(percentage_score - previous_percent, 2)
        trend = "improved" if delta_percent > 0 else "declined"
        feedback += f"You have {trend} by {abs(delta_percent)}% since your last interview.\n\n"

    # Percentile calculation
    all_percentages = [
        round((avg * num_questions / max_total) * 100, 2)
        for uid, avg in all_scores
    ]

    all_percentages.sort(reverse=True)
    user_rank = all_percentages.index(percentage_score) + 1
    total_users = len(all_percentages)
    percentile = round((1 - (user_rank - 1) / total_users) * 100)

    if total_users > 1:
        feedback += f"You're in the top {percentile}% of candidates in the same domain."
    else:
        feedback += "You are the first candidate in this domain — no peer comparison yet."

    return feedback
