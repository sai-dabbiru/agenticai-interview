from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.tools import Tool
from tools.vectorstore import load_interview_vectorstore
from agents.domain_classifier import classify_role_to_domain

chat_llm = ChatOpenAI(model="gpt-4", temperature=0.4)

with open("prompts/rag_prompt.txt", "r") as f:
    rag_template = f.read()

rag_prompt = ChatPromptTemplate.from_template(rag_template)

def generate_interview_question(input_str: str) -> str:
    role, experience = input_str.split("|")
    vectorstore = load_interview_vectorstore()
    domain = classify_role_to_domain(role)

    results = vectorstore.similarity_search_with_score(domain, k=5)

    # Define a similarity threshold (lower score = better match in most vector DBs)
    SIMILARITY_THRESHOLD = 0.7  # Adjust based on embedding backend

    for doc, score in results:
        if doc.metadata.get("domain") == domain and score < SIMILARITY_THRESHOLD:
            return doc.page_content

    return f"No suitable interview question found for the domain: {domain}."

interview_question_tool = Tool(
    name="InterviewQuestionGenerator",
    func=generate_interview_question,
    description="Generates a technical interview question based on role and experience. Input format: 'role|experience'"
)
