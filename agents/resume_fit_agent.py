from langchain.tools import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from tools.resume_parser import load_resume_text
from configs.settings import OPENAI_API_KEY, MODEL_NAME

chat_llm = ChatOpenAI(model=MODEL_NAME, temperature=0.3)

with open("prompts/resume_fit_prompt.txt", "r") as f:
    prompt_template = f.read()

prompt = ChatPromptTemplate.from_template(prompt_template)

def run_resume_fit(input_str: str) -> str:
    # input_str format: "path|role|experience"
    path, role, exp = input_str.split("|")
    resume_text = load_resume_text(path)
    messages = prompt.format_messages(resume=resume_text, target_role=role, experience=exp)
    response = chat_llm(messages)
    return response.content

resume_fit_tool = Tool(
    name="ResumeFitEvaluator",
    func=run_resume_fit,
    description="Evaluates a resume (input: 'path|role|experience') and returns fit score + feedback."
)
