# agent.py
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from tools import get_all_tables
import os

load_dotenv()

def load_agent(tables: list = None):
    db = SQLDatabase.from_uri(
        "sqlite:///data/amazon.db",
        include_tables=tables or get_all_tables(),
        sample_rows_in_table_info=3
    )

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )

    agent = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="zero-shot-react-description",
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10
    )

    print("✅ Agent loaded successfully!")
    return agent

def ask(agent, question: str) -> tuple[str, str]:
    """Returns (answer, sql_used)"""
    try:
        # Capture verbose output to extract SQL
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            response = agent.invoke({"input": question})

        verbose_output = f.getvalue()

        # Extract SQL from verbose output
        sql = ""
        for line in verbose_output.split("\n"):
            if "Action Input:" in line and "SELECT" in line.upper():
                sql = line.replace("Action Input:", "").strip()
                break

        return response["output"], sql

    except Exception as e:
        return f"❌ Error: {str(e)}", ""