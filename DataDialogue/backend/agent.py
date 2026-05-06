import json
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from backend.config import ANTHROPIC_API_KEY
from backend import database as db

@tool
def inspect_schema(placeholder: str = "") -> str:
    """Returns the comple Corp database schema, all tables, all columns, data types and row counts and relationships
    ALWAYS call this first before writing any SQL query.
    You must know the schema before you can query anything. Input: empty string (no input needed)"""
    return db.get_schema()

@tool
def get_sample_rows(table_name: str) -> str:
    """Returns 3 sample rows from a specific table, Use this when you need to understand what values a column contains before filtering or grouping.
    Example: call this on 'customers' to see what values 'industry' or 'tier' column contain.
      Input: table name as a string e.g: 'customers', 'deals' """
    return db.get_sample_rows(table_name)

@tool
def run_query(sql: str) -> str:
    """"Validates and executes a SQL SELECT query against the Corp database. Returns results as formatted text.
    Only use after inspecting the schema first. Only SELECT queries are allowed - No INSERT, UPDATE, DELETE.
    Always write clean, efficient SQL with proper JOINs. Input: a valid SQL SELECT statement"""

    result = db.run_query(sql)

    if not result["success"]:
        return f"Query failed: {result['error']}\nSQL attempted: {result['sql_used']}"

    if result["row_count"] == 0:
        return f"Query returned no results.\nSQL: {result['sql_used']}"
    
    output = ""
    display_rows = result["rows"][:50]
    for row in display_rows:
        output += " | ".join(str(v) for v in row) + "\n"

    if result["row_count"] > 50:
        output += f"\n... and {result['row_count'] - 50} more rows."

    # Always append the SQL so Claude can reference it
    output += f"\n\nSQL used:\n{result['sql_used']}"

    return output

@tool
def get_query_history(limit: int = 5) -> str:
    """ Returns the most recent queries from the current session.
    Use this when the user asks about previous questions,
    wants to re-run a query, or refers to 'that last query'.
    Input: number of recent queries to return (default 5) """
    if not _current_session_history:
        return "No queries in this session yet."
    output = f"Recent queries this session:\n\n"
    for i, entry in enumerate(_current_session_history[-limit:], 1):
        output += f"{i}. {entry['question']}\n"
        output += f"   SQL: {entry['sql'][:80]}...\n"
        output += f"   Rows: {entry['row_count']}\n\n"
    return output

_current_session_history = []

# SYSTEM PROMPT
SYSTEM_PROMPT = """You are DataDialogue, an expert AI data analyst
for NexaCorp — a B2B SaaS company.

You help business users query the Corp database using plain English.
You translate their questions into SQL, run the queries, and explain
the results in clear business terms.

YOUR WORKFLOW (follow this every time):
1. ALWAYS call inspect_schema first to understand the database
2. If unsure about column values, call get_sample_rows
3. Write the SQL query mentally before calling run_query
4. Call run_query with the SQL
5. Explain the results in plain business English
6. Suggest 1-2 relevant follow-up questions

SQL RULES (never break these):
- Only write SELECT queries — never INSERT, UPDATE, DELETE, DROP
- Always use table aliases for readability: customers c, deals d
- Always use proper JOINs — never comma-separated tables
- Handle NULL values with COALESCE where appropriate
- For date filtering use: WHERE close_date >= '2024-01-01'
- For aggregations always include GROUP BY
- Limit large results with LIMIT 100 unless user asks for all

NEXACORP CONTEXT:
- deals.stage: 'closed_won' or 'closed_lost'
- customers.tier: 'enterprise', 'mid-market', 'smb'
- customers.mrr: monthly recurring revenue in USD
- monthly_targets.attainment_pct: actual/target * 100

RESPONSE FORMAT:
- Lead with the business insight, not the technical details
- Show the SQL in a code block so users can verify it
- If results are empty, explain why and suggest alternatives
- Always end with 1-2 follow-up question suggestions

You are read-only. You cannot modify any data."""

TOOLS = [
    inspect_schema,
    get_sample_rows,
    run_query,
    get_query_history
]


def create_agent():
    llm = ChatAnthropic(model ="claude-sonnet-4-6", api_key = ANTHROPIC_API_KEY,temperature = 0, max_tokens =4000)
    return create_react_agent(llm, TOOLS, prompt = SYSTEM_PROMPT)

chat_histories = {}
session_query_history = {}
last_results = {}

def chat(user_message: str, session_id: str="default") -> dict:
    """ Additional responsibility : capture the SQl query result so the frontend can render the results table and the [Explain this] button has data to work with."""
    global _current_session_history
    agent = create_agent()
    history = chat_histories.get(session_id,[])

    _current_session_history = session_query_history.get(session_id,[])
    result = agent.invoke({"messages": history + [HumanMessage(content=user_message)]})
    response_text = result["messages"][-1].content

    history.append(HumanMessage(content=user_message))
    history.append(AIMessage(content=response_text))
    chat_histories[session_id] = history

    agent_action = "general_purpose"
    query_result = None

    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                agent_action = tc['name']
        
        if hasattr(msg, "name") and msg.name == "run_query":
            pass

    sql_used = None
    columns = []
    rows = []
    row_count = 0

    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc["name"] == "run_query":
                    sql_used = tc["args"].get("sql", "")
                    # Run again to get structured data for UI
                    qr = db.run_query(sql_used)
                    if qr["success"]:
                        columns   = qr["columns"]
                        rows      = qr["rows"]
                        row_count = qr["row_count"]

                        # Update session query history
                        sq_history = session_query_history.get(session_id, [])
                        sq_history.append({
                            "question":  user_message,
                            "sql":       sql_used,
                            "row_count": row_count
                        })
                        session_query_history[session_id] = sq_history

                        # Store last result for /explain endpoint
                        last_results[session_id] = {
                            "sql":      sql_used,
                            "columns":  columns,
                            "rows":     rows,
                            "question": user_message
                        }

                        # Log to database
                        db.log_query(
                            session_id    = session_id,
                            user_question = user_message,
                            sql_generated = sql_used,
                            row_count     = row_count,
                            exec_ms       = qr["exec_ms"],
                            success       = True
                        )

    # Log audit
    db.log_audit(
        session_id    = session_id,
        user_question = user_message,
        agent_action  = agent_action,
        full_response = response_text
    )

    return {
        "response":   response_text,
        "sql_used":   sql_used,
        "columns":    columns,
        "rows":       rows,
        "row_count":  row_count,
        "agent_action": agent_action,
        "session_id": session_id
    }

def explain_result(session_id: str) -> str:
    """
    Called when user clicks [Explain this] button.
    Takes the last query result and asks Claude to
    interpret it in business terms.
    No tools needed — pure Claude reasoning.
    """
    last = last_results.get(session_id)
    if not last:
        return "No query results to explain yet. Ask a question first."

    llm = ChatAnthropic(
    model  = "claude-sonnet-4-6",
    api_key = ANTHROPIC_API_KEY,
    temperature = 0,
    max_tokens  = 1000
    )

    # Build a summary of the results for Claude to interpret
    rows_preview = last["rows"][:10]
    rows_text    = "\n".join(
        [" | ".join(str(v) for v in row) for row in rows_preview]
    )

    prompt = f"""A business user asked: "{last['question']}"

The query returned these results:
Columns: {', '.join(last['columns'])}
{rows_text}
{'...' if len(last['rows']) > 10 else ''}
Total rows: {len(last['rows'])}

Please provide:
1. A clear business interpretation of what these results mean
2. The key insight or takeaway in one sentence
3. Any anomalies or interesting patterns you notice
4. One concrete business action this data suggests

Keep it concise and business-focused. No technical jargon."""

    response = llm.invoke(prompt)
    return response.content
