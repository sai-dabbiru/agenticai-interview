from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.tools import Tool
from tools.vectorstore import load_interview_vectorstore
from agents.domain_classifier import classify_role_to_domain

chat_llm = ChatOpenAI(model="gpt-4", temperature=0.4)

with open("prompts/rag_prompt.txt", "r") as f:
    rag_template = f.read()

rag_prompt = ChatPromptTemplate.from_template(rag_template)

# def generate_interview_question(input_str: str) -> str:

#     role, experience = input_str.split("|")
#     vectorstore = load_interview_vectorstore()
#     domain = classify_role_to_domain(role).strip().lower()

#     print("\n[DEBUG] -----------------------------")
#     print(f"[DEBUG] Input Role: {role}")
#     print(f"[DEBUG] Classified Domain: {domain}")
#     print("[DEBUG] Performing vector similarity search...")
    
#     results = vectorstore.similarity_search_with_score(domain, k=10)

#     print("[DEBUG] Raw search results (content + domain):")
#     for doc, score in results:
#         print(f" - Score: {score:.4f}, Domain: {doc.metadata.get('domain')}, Content: {doc.page_content[:60]}...")

#     # Post-filter by domain match
#     filtered_results = []
#     for doc, score in results:
#         doc_domain = doc.metadata.get("domain", "").strip().lower()
#         if doc_domain == domain:
#             filtered_results.append((doc, score))

#     print(f"[DEBUG] Filtered results for domain '{domain}': {len(filtered_results)} found.")
#     for doc, score in filtered_results:
#         print(f" - Selected Question: {doc.page_content[:60]}...")

#     if not filtered_results:
#         print(f"[DEBUG] No question found for domain: {domain}")
#         return f"No suitable interview question found for the domain: {domain}."

#     # Return top filtered doc
#     best_doc = sorted(filtered_results, key=lambda x: x[1])[0][0]
#     print(f"[DEBUG] Returning top question for domain '{domain}'.")
#     print("[DEBUG] -----------------------------\n")

#     return best_doc.page_content

def generate_interview_question(input_str: str, already_asked: list[str] = None) -> str:
    already_asked = already_asked or []
    print(already_asked)
    
    role, experience = input_str.split("|")
    vectorstore = load_interview_vectorstore()
    domain = classify_role_to_domain(role).strip().lower()

    print("\n[DEBUG] -----------------------------")
    print(f"[DEBUG] Input Role: {role}")
    print(f"[DEBUG] Classified Domain: {domain}")
    print("[DEBUG] Performing vector similarity search...")

    results = vectorstore.similarity_search_with_score(domain, k=10)

    print("[DEBUG] Raw search results (content + domain):")
    for doc, score in results:
        print(f" - Score: {score:.4f}, Domain: {doc.metadata.get('domain')}, Content: {doc.page_content[:60]}...")

    # Post-filter by domain and already asked
    filtered_results = []
    for doc, score in results:
        doc_domain = doc.metadata.get("domain", "").strip().lower()
        if doc_domain == domain and doc.page_content not in already_asked:
            filtered_results.append((doc, score))

    print(f"[DEBUG] Filtered results for domain '{domain}' (excluding asked): {len(filtered_results)} found.")
    for doc, score in filtered_results:
        print(f" - Available Question: {doc.page_content[:60]}...")

    if not filtered_results:
        print(f"[DEBUG] No NEW question found for domain: {domain}")
        return f"No suitable interview question found for the domain: {domain}."

    best_doc = sorted(filtered_results, key=lambda x: x[1])[0][0]
    print(f"[DEBUG] Returning top NEW question for domain '{domain}'.")
    print("[DEBUG] -----------------------------\n")

    return best_doc.page_content



interview_question_tool = Tool(
    name="InterviewQuestionGenerator",
    func=generate_interview_question,
    description="Generates a technical interview question based on role and experience. Input format: 'role|experience'"
)
