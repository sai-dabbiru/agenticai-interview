# services/mock_interview_controller.py

from agents.resume_fit_agent import resume_fit_tool
from agents.interview_agent import interview_question_tool 
from agents.feedback_agent import evaluate_answer

class MockInterviewSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.role = None
        self.experience = None
        self.resume_score = None
        self.feedback = None
        self.asked_questions = []
        self.answers = []
        self.current_question = None

    def should_start_interview(self):
        return self.resume_score is not None and self.resume_score >= 70


    def process_resume(self, resume_path, role, experience):
        self.role = role
        self.experience = experience
        result = resume_fit_tool.run(f"{resume_path}|{role}|{experience}")
        self.resume_score = self._extract_score(result)
        self.feedback = result
        return self.resume_score, self.feedback
    
    def _extract_score(self, result):
        import json
        try:
            parsed = json.loads(result)
            return parsed.get("score", 0)
        except Exception:
            import re
            match = re.search(r"[Ss]core\s*[:\-]?\s*(\d+)", result)
            return int(match.group(1)) if match else 0
    
    def generate_question(self):
        from tools.vectorstore import load_interview_vectorstore
        from agents.domain_classifier import classify_role_to_domain

        domain = classify_role_to_domain(self.role)
        vectorstore = load_interview_vectorstore()

        results = vectorstore.similarity_search_with_score(domain, k=5)

        for doc, score in results:
            q = doc.page_content
            if q not in self.asked_questions:
                self.asked_questions.append(q)
                self.current_question = q
                return q

        return "No more questions available for your role."

    def submit_answer(self, answer: str):
        self.answers.append({
            "question": self.current_question,
            "answer": answer
        })

    def evaluate_all_answers(self):
        self.feedback = []
        total_score = 0
        for pair in self.answers:
            q = pair["question"]
            a = pair["answer"]
            result = evaluate_answer(q, a)
            self.feedback.append(result)
            total_score += result.get("score", 0)
        return total_score, self.feedback