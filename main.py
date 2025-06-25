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

MAX_QUESTIONS = 3

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
        score, feedback = session.process_resume(file_path, target_role, experience)

        result = {
            "user_id": user_id,
            "status": "pass" if score >= 70 else "fail",
            "score": score,
            "feedback": feedback,
        }

        # 🚀 Automatically fetch first interview question if eligible
        if session.should_start_interview():
            result["next_step"] = "interview"
            result["question"] = session.generate_question()
        else:
            result["next_step"] = "retry"  # or "improve resume"

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
        session.submit_answer(answer)

        if len(session.asked_questions) >= MAX_QUESTIONS:
            # ✅ Interview done, save to DB
            save_session(session)
            return JSONResponse(content={
                "status": "completed",
                "message": "Interview completed. Session saved.",
                "question_count": len(session.asked_questions)
            })

        # Otherwise continue
        next_q = session.generate_question()
        return JSONResponse(content={
            "next_question": next_q,
            "question_count": len(session.asked_questions)
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
