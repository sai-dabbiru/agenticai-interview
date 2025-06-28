from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

chat_llm = ChatOpenAI(model="gpt-4", temperature=0)

feedback_prompt_template = ChatPromptTemplate.from_template("""
You're a mock interview evaluator.

Evaluate the following answer:
Question: {question}
Answer: {answer}

Respond with a JSON object having:
- score: (integer 0-5)
- feedback: (short, constructive and what could be done better to improve)

Example:
{{"score": 4, "feedback": "good explanation but could improve on technical details which would be needed for client facing roles."}}

Only output the JSON.
""")

def evaluate_answer(question: str, answer: str) -> dict:
    messages = feedback_prompt_template.format_messages(
        question=question,
        answer=answer
    )
    response = chat_llm(messages).content

    import json
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"score": 0, "feedback": "Unable to evaluate answer reliably."}
