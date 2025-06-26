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
    results = vectorstore.similarity_search_with_score(domain, k=10)

    # STRICT FILTERING: Post-filter results based on domain match
    domain_matches = [
        (doc, score)
        for doc, score in results
        if doc.metadata.get("domain", "").strip().lower() == domain.lower()
    ]

    if not domain_matches:
        return f"No suitable interview question found for the domain: {domain}."

    # Optional: Sort by score if needed
    best_doc = sorted(domain_matches, key=lambda x: x[1])[0]
    return best_doc[0].page_content

interview_question_tool = Tool(
    name="InterviewQuestionGenerator",
    func=generate_interview_question,
    description="Generates a technical interview question based on role and experience. Input format: 'role|experience'"
)
