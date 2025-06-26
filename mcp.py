import asyncio
import sqlite3
import os
from pathlib import Path
from typing import Optional

# Force OpenAI usage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

# Configuration - Force OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_PATH = "data/interviews.db"

# MCP adapters (optional)
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    print("⚠️ MCP adapters not available. Using direct SQLite integration.")
    MCP_AVAILABLE = False

class SQLiteMCPDemo:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.client = None
        self.agent = None
        
    def setup_database(self):
        """Check if interview.db exists and show its structure"""
        if not os.path.exists(self.db_path):
            print(f"❌ Database {self.db_path} not found!")
            print("Please make sure your interview.db file is in the current directory.")
            return False
        
        print(f"✅ Found database: {self.db_path}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if tables:
                print(f"📋 Found {len(tables)} table(s):")
                for table in tables:
                    table_name = table[0]
                    print(f"  - {table_name}")
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"    ({count} rows)")
            else:
                print("⚠️ No tables found in the database")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error reading database: {e}")
            return False

    def get_mcp_server_config(self) -> dict:
        return {
            "sqlite-server": {
                "command": "python",
                "args": ["-m", "mcp_server_sqlite", "--db-path", self.db_path],
                "env": {}
            }
        }
    
    async def initialize_mcp_client(self):
        try:
            self.client = MultiServerMCPClient()
            tools = []
            print("🔄 Initializing MCP client...")
            return tools
        except Exception as e:
            print(f"⚠️ Error initializing MCP client: {e}")
            return []

    def create_direct_sqlite_tool(self):
        @tool
        def query_sqlite_db(query: str) -> str:
            """Execute SELECT query against only 'interview_sessions' table."""
            query_upper = query.strip().upper()
            if not query_upper.startswith('SELECT'):
                return "❌ Error: Only SELECT queries are allowed."
            if "INTERVIEW_SESSIONS" not in query_upper:
                return "❌ Error: You are only allowed to query the 'interview_sessions' table."
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(query)
                results = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                if not results:
                    return "No results found."
                output = []
                output.append(" | ".join(column_names))
                output.append("-" * len(output[0]))
                for row in results:
                    output.append(" | ".join(str(cell) for cell in row))
                conn.close()
                return "\n".join(output)
            except sqlite3.Error as e:
                return f"❌ Database error: {e}"
            except Exception as e:
                return f"❌ Error: {e}"

        @tool
        def describe_tables() -> str:
            """Describe schema of all tables (optional fallback)."""
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                result = []
                for table in tables:
                    table_name = table[0]
                    result.append(f"\n📋 Table: {table_name}")
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    for col in columns:
                        col_name, col_type, not_null, default, pk = col[1], col[2], col[3], col[4], col[5]
                        pk_indicator = " (PRIMARY KEY)" if pk else ""
                        not_null_indicator = " NOT NULL" if not_null else ""
                        result.append(f"  - {col_name}: {col_type}{not_null_indicator}{pk_indicator}")
                conn.close()
                return "\n".join(result)
            except Exception as e:
                return f"Error describing tables: {e}"

        return [query_sqlite_db, describe_tables]

    async def create_agent(self):
        if not OPENAI_API_KEY:
            raise ValueError("❌ Please set OPENAI_API_KEY environment variable")
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        print("✅ Using OpenAI GPT-3.5-turbo")

        if MCP_AVAILABLE:
            mcp_tools = await self.initialize_mcp_client()
        else:
            mcp_tools = []
        
        tools = self.create_direct_sqlite_tool()
        self.agent = create_react_agent(llm, tools)
        print("🤖 Agent created successfully with OpenAI!")

    async def interactive_mode(self):
        if not self.agent:
            raise ValueError("Agent not initialized. Call create_agent() first.")
        
        print("\n" + "="*60)
        print("💬 Interactive Mode - Ask questions about 'interview_sessions' table only.")
        print("💡 Examples:")
        print("   - 'Show all records from interview_sessions'")
        print("   - 'What are the distinct values in column x?'")
        print("   - 'Find all sessions after a given date'")
        print("   - Type 'quit' to exit")
        print("="*60)
        
        while True:
            try:
                user_query = input("\n🤔 Your question: ").strip()
                if user_query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                if not user_query:
                    continue
                print("🤖 Thinking...")
                response = await self.agent.ainvoke(
                    {"messages": [HumanMessage(content=user_query)]}
                )
                final_message = response["messages"][-1]
                print(f"🤖 Response: {final_message.content}")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

async def main():
    print("🎯 SQLite MCP Adapter Demo with interview.db")
    print("="*50)
    
    demo = SQLiteMCPDemo()
    
    if not demo.setup_database():
        print("\n❌ Cannot proceed without the database file.")
        return

    try:
        await demo.create_agent()
    except ValueError as e:
        print(f"\n{e}")
        return

    await demo.interactive_mode()

def create_mcp_config_file():
    config = {
        "mcpServers": {
            "sqlite": {
                "command": "uvx",
                "args": ["mcp-server-sqlite", "--db-path", "interview.db"]
            }
        }
    }
    import json
    with open("mcp_config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("📄 MCP configuration file created: mcp_config.json")

if __name__ == "__main__":
    create_mcp_config_file()
    asyncio.run(main())
