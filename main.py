import os
import json # Import the json module
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from agents.resume_fit_agent import resume_fit_tool
from langchain.agents import initialize_agent, AgentType
from services.session_store import get_session
from agents.interview_agent import interview_question_tool
from services.db import init_db
from services.db import save_session
from agents.feedback_agent import evaluate_answer
from agents.progress_tracker import generate_progress_feedback
from agents.classifier_agent import classify_user_intent
from agents.admin_agent import get_admin_agent
from langchain_core.messages import HumanMessage

MAX_QUESTIONS = 3
admin_agent = get_admin_agent()

init_db()
app = FastAPI()

# Configure CORS middleware
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "*" # Allows requests from any origin for development purposes
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all standard methods
    allow_headers=["*"], # Allows all headers
)

# Initialize the agent with the resume fit tool
agent = initialize_agent(
    tools=[resume_fit_tool,interview_question_tool],
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    llm=resume_fit_tool.func.__globals__["chat_llm"],  # Get the LLM used in the tool
    verbose=True
)

@app.post("/agent/resume_evaluate")
async def evaluate_resume_api(
    user_id: str = Form(...),
    target_role: str = Form(...),
    experience: str = Form(...),
    skills: str = Form(...),
    resume: UploadFile = Form(...)
):
    try:
        folder = "data/resumes"
        os.makedirs(folder, exist_ok=True)

        file_name = os.path.basename(resume.filename) or "uploaded_resume.pdf"
        file_path = os.path.join(folder, file_name)

        with open(file_path, "wb") as f:
            f.write(await resume.read())

        session = get_session(user_id)
        score, feedback = session.process_resume(file_path, target_role, experience,skills)

        result = {
            "user_id": user_id,
            "status": "pass" if score >= 70 else "fail",
            "score": score,
            "feedback": feedback,
        }

        if session.should_start_interview():
            question = session.generate_question()
            if "No more questions available" in question or "No suitable interview question" in question:
                result["next_step"] = "retry"
                result["message"] = question  
            else:
                result["next_step"] = "interview"
                result["question"] = question
        else:
            result["next_step"] = "retry"  

        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/agent/interview_question")
async def get_mock_question(
    target_role: str = Form(...),
    experience: str = Form(...)
):
    try:
        input_str = f"{target_role}|{experience}"
        prompt = f"Generate a technical interview question for this candidate: {input_str}"
        response = agent.run(prompt)
        return JSONResponse(content={"question": response})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    

@app.post("/agent/submit_answer")
async def submit_answer_api(
    user_id: str = Form(...),
    answer: str = Form(...)
):
    try:
        session = get_session(user_id)

        # 👇 Get the latest asked question to evaluate the answer
        current_question = session.asked_questions[-1] if session.asked_questions else "Unknown"
        session.submit_answer(answer)

        # ✅ Evaluate feedback for this specific question
        single_feedback = evaluate_answer(current_question, answer)

        # 🛡️ Safely initialize feedback list (handles JSON string from DB)
        import json
        if not hasattr(session, "feedback") or not isinstance(session.feedback, list):
            try:
                session.feedback = json.loads(session.feedback) if isinstance(session.feedback, str) else []
            except:
                session.feedback = []
        session.feedback.append(single_feedback)

        # ✅ If this was the last question
        if len(session.asked_questions) >= MAX_QUESTIONS:
            # Save full session (questions, answers, feedback)
            save_session(session)

            # Generate progress insight
            progress = generate_progress_feedback(user_id, session.role)

            return JSONResponse(content={
                "status": "completed",
                "individual_feedback": single_feedback,
                "progress_feedback": progress
            })

        # ✅ Else generate the next question
        next_q = session.generate_question()

        return JSONResponse(content={
            "status": "in_progress",
            "next_question": next_q,
            "question_count": len(session.asked_questions),
            "individual_feedback": single_feedback
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})



@app.get("/agent/history")
async def get_user_history(user_id: str):
    session = get_session(user_id)
    return JSONResponse(content={
        "questions": session.asked_questions,
        "answers": session.answers
    })

@app.get("/agent/feedback_summary")
async def feedback_summary(user_id: str):
    try:
        session = get_session(user_id)
        total_score, feedback = session.evaluate_all_answers()

        # 🧠 Persist with feedback
        if not session.is_saved:
            from services.db import save_session
            save_session(session)
            session.is_saved = True 

        return JSONResponse(content={
            "user_id": user_id,
            "total_score": total_score,
            "average_score": round(total_score / len(feedback), 2) if feedback else 0,
            "individual_feedback": feedback
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/agent/progress")
async def progress_api(user_id: str, role: str):
    try:
        insight = generate_progress_feedback(user_id, role)
        return JSONResponse(content={"progress_feedback": insight})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    

@app.post("/agent/classify_and_route")
async def classify_and_route(user_id: str = Form(...), query: str = Form(...)):

    intent = classify_user_intent(query)
    print(f"Classified intent: {intent}")

    if intent == "interview":
        return JSONResponse(content={
            "action": "interview"
        })

    elif intent == "reflect":
        return JSONResponse(content={
            "action": "reflect"
        })
    

    else:
        return JSONResponse(content={
        "action": "unknown"
    })


@app.post("/agent/admin_query")
async def admin_query(query: str = Form(...)):
    try:
        result = await admin_agent.ainvoke({"messages": [HumanMessage(content=query)]})
        final_response = result["messages"][-1].content
        return JSONResponse(content={"response": final_response})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})