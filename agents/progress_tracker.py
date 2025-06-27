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
        SELECT user_id, resume_score, feedback
        FROM interview_sessions
    """)
    rows = cursor.fetchall()
    conn.close()

    peer_scores = []
    user_scores = []


    for uid, resume_score, feedback_json in rows:
        try:
            feedback = json.loads(feedback_json)
            total = sum(item.get("score", 0) for item in feedback)
            avg = total / len(feedback) if feedback else 0
        except:
            avg = 0

        if avg > 0:
            peer_scores.append(avg)
            if uid == user_id:
                user_scores.append(avg)

    return user_scores, peer_scores



# def generate_progress_feedback(user_id: str, role: str):
#     user_scores, peer_scores = get_user_and_peer_scores(user_id, role)

#     if not user_scores:
#         return "No prior interview sessions found."

#     current_score = user_scores[-1]
#     previous_score = user_scores[-2] if len(user_scores) > 1 else None
#     peer_avg = statistics.mean(peer_scores) if peer_scores else 0

#     feedback = f"Your current score is {current_score:.2f}. "

#     if previous_score:
#         delta = current_score - previous_score
#         trend = "improved" if delta > 0 else "declined"
#         feedback += f"You have {trend} by {abs(delta):.2f} points since your last interview. "

#     if peer_avg:
#         delta = current_score - peer_avg
#         comparison = "above" if delta > 0 else "below"
#         feedback += f"You're {abs(delta):.2f} points {comparison} the average score of others in the same domain."

#     return feedback

def generate_progress_feedback(user_id: str, role: str):
    user_scores, peer_scores = get_user_and_peer_scores(user_id, role)

    if not user_scores:
        return "No prior interview sessions found."

    current_score = user_scores[-1]
    previous_score = user_scores[-2] if len(user_scores) > 1 else None

    # Assume max score per question is 5
    max_per_question = 5
    num_questions = 3  # ⬅️ This should ideally come from saved session length

    max_total = max_per_question * num_questions
    total_score = round(current_score * num_questions, 2)  # Since current_score is average per question
    percentage_score = round((total_score / max_total) * 100, 2)

    feedback = f"Your current score is {total_score}/{max_total} ({percentage_score}%). "

    if previous_score:
        delta = current_score - previous_score
        trend = "improved" if delta > 0 else "declined"
        feedback += f"You have {trend} by {abs(delta):.2f} points since your last interview. "

    if peer_scores and len(peer_scores) > 1:
        peer_avg = statistics.mean([s for s in peer_scores if s != current_score])
        delta = current_score - peer_avg
        comparison = "above" if delta > 0 else "below"
        feedback += f"You're {abs(delta):.2f} points {comparison} the average score of others in the same domain."
    else:
        feedback += "No peer comparison is available yet."

    return feedback
