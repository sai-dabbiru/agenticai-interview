# services/session_store.py

_sessions = {}

def get_session(user_id: str):
    from services.mock_interview_controller import MockInterviewSession
    if user_id not in _sessions:
        _sessions[user_id] = MockInterviewSession(user_id)
    return _sessions[user_id]
