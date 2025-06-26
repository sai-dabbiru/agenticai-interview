from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

chat_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

classifier_prompt = ChatPromptTemplate.from_template("""
Classify the user's intent based on their message.

User message: "{query}"

Choose one of these categories:
- "interview": user wants to start or continue a mock interview
- "reflect": user wants to analyze past performance, understand weaknesses, get skill improvement tips, receive feedback, or review their progress
- "admin" : user wants to access leaderboard , stats , or other administrative tasks                                                  

Respond with just the category name.
""")

def classify_user_intent(query: str) -> str:
    messages = classifier_prompt.format_messages(query=query)
    return chat_llm(messages).content.strip().lower()
