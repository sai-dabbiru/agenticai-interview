from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

chat_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

prompt_template = """
Classify the following role into one of these domains: devops, frontend, backend, data, cloud, security.

Role: {role}

Respond with only the domain (e.g., 'devops').
"""

classifier_prompt = ChatPromptTemplate.from_template(prompt_template)

def classify_role_to_domain(role: str) -> str:
    messages = classifier_prompt.format_messages(role=role)
    response = chat_llm(messages)
    return response.content.strip().lower()
