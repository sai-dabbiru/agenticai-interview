import os
import sqlite3
from typing import List
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

DB_PATH = "data/interviews.db"

@tool
def query_sqlite_db(query: str) -> str:
    """Execute SELECT query against only 'interview_sessions' table."""
    query_upper = query.strip().upper()
    if not query_upper.startswith('SELECT'):
        return "❌ Only SELECT queries are allowed."
    if "INTERVIEW_SESSIONS" not in query_upper:
        return "❌ Only 'interview_sessions' table is allowed."

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()

        if not results:
            return "No results found."

        output = [" | ".join(columns), "-" * 30]
        for row in results:
            output.append(" | ".join(str(cell) for cell in row))
        return "\n".join(output)
    except Exception as e:
        return f"❌ Error: {e}"

@tool
def describe_tables() -> str:
    """Describe schema of all tables."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        result = []
        for (table_name,) in tables:
            result.append(f"\n📋 Table: {table_name}")
            cursor.execute(f"PRAGMA table_info({table_name});")
            for col in cursor.fetchall():
                result.append(f"  - {col[1]}: {col[2]}")
        conn.close()
        return "\n".join(result)
    except Exception as e:
        return f"❌ Error describing tables: {e}"

def get_admin_agent():
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    tools = [query_sqlite_db, describe_tables]
    return create_react_agent(llm, tools)
