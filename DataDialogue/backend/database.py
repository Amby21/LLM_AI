import sqlite3
import json
import time
from datetime import datetime
from backend.config import SAMPLE_DB_PATH, APP_DB_PATH
from backend.safety import validate_sql, sanitise_sql
#%%

def get_sample_connection():
    """Opens a READ-ONLY connection to the Corp database. uri = True enables SQLite URI syntax. ?mode=ro makes it physically read-only
    at OS level. Even if code accidentally tries to write - it fails.
    This is the third safety layer afer:
    1: System prompt (dont't write destructive SQL)
    2. safety.py validation(reject non-SELECT sql)
    3. This read-only connection (OS-level rejection)
    """
    uri = f"file:{SAMPLE_DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri,uri=True,check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_schema() -> str:
    """Return the complete database schema as a formatted string.
    This is the FIRST thing the agent calls before any query. This is used to understand:
    1: what tables exist
    2: what columns each table has.
    3: what data types each column is.
    4: what foreign key relationships exist.
    with this the LLM know what to query."""

    conn = get_sample_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT name FROM sqlite_master
                    WHERE type='table'
                ORDER BY name """)
    tables = [row["name"] for row in cursor.fetchall()]

    schema_text = "Corp Database Schema \n"
    schema_text += "=" *50 +"\n\n"

    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()

        #row count for database size
        cursor.execute(f"SELECT COUNT(*) AS cnt FROM {table}")
        row_count = cursor.fetchone()["cnt"]
        schema_text += f"TABLE: {table} ({row_count} rows)\n"
        schema_text += "-" * 30 + "\n"

        for col in columns:
            pk_marker = "[PRIMARY KEY]" if col["pk"] else "" 
            schema_text += (f" {col['name']}: {col['type']}{pk_marker}\n")

        # get foreign key relationships
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fkeys = cursor.fetchall()
        if fkeys:
            schema_text += "Relationships:\n"
            for fk in fkeys:
                schema_text += ( f"{fk['from']} -> {fk['table']}.{fk['to']}\n")
                schema_text +="\n"

    conn.close()
    return schema_text

def get_sample_rows(table_name: str, limit: int = 3) -> str:
    """" Returns sample rows from a table as formatted text. LLM uses this to understand what values look like.
    Example: column "tier" - what are valid values? Sample rows reveal: "enterprise", "mid-market", "smb"
    Without sample data, LLM might gueses wrong column values.
    """
    conn = get_sample_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name=?""", (table_name,))

    if not cursor.fetchone():
        conn.close()
        return f"Table '{table_name}' does not exist"
    
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    conn.close()

    if not rows:
        return f"Table '{table_name}' is empty"
    output = f" Sample data from '{table_name}':\n"
    output += "| ".join(columns) + "\n"
    output += "-" * 60 + "\n"
    
    for row in rows:
        output += "|".join (str(v) for v in row) + "\n"
    
    return output

def run_query(sql:str) ->dict:
    """The main query execution function. Sanitise,Validate,Execute, Return as dictionary."""

    sql = sanitise_sql(sql)

    validation = validate_sql(sql)
    if not validation["safe"]:
        return {"success": False,"sql_used": sql,"columns":[],"rows":[],"rows_count":0,"error": validation["reason"],"exec_ms":0}
    
    conn = get_sample_connection()
    cursor = conn.cursor()

    start = time.time()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [d[0] for d in cursor.description] if cursor.description else[]
        exec_ms = int((time.time()-start) *1000)

        rows_list = [list(row) for row in rows]
        conn.close()
        return {"success":   True,
            "sql_used":  sql,
            "columns":   columns,
            "rows":      rows_list,
            "row_count": len(rows_list),
            "error":     None,
            "exec_ms":   exec_ms }
    except Exception as e:
        conn.close()
        return{  "success":   False,
            "sql_used":  sql,
            "columns":   [],
            "rows":      [],
            "row_count": 0,
            "error":     str(e),
            "exec_ms":   0}
######################################################
# APP Database
def get_app_connection():
    """Standard read/write connection to the app database."""
    conn = sqlite3.connect(APP_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def log_query(session_id: str, user_question: str, sql_generated: str, row_count: int, exec_ms: int, success: bool, error_message: str = None):
    """Records every SQL query to the query_log_table. Called after every run_query() execution. This is the governance layer"""
    conn = get_app_connection()
    cursor = conn.cursor()
    cursor.execute(""" INSERT INTO query_log(session_id, user_question, sql_generated, row_count, execution_ms, success,error_message) VALUES (?,?,?,?,?,?,?)""",(session_id, user_question, sql_generated, row_count, exec_ms,1 if success else 0, error_message))
    conn.commit()
    conn.close()

def log_audit(session_id: str, user_question: str, agent_action: str, full_response: str):
    """Records every agent action to the audit log."""
    conn = get_app_connection()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO audit_log(session_id, user_question, agent_action, full_response) VALUES (?,?,?,?)""", (session_id, user_question, agent_action, full_response))
    conn.commit()
    conn.close()

def get_schema_for_api() -> list:
    """Returns schema as a structured list for the frontend schema explorer panel."""
    conn = get_sample_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT name FROM sqlite_master WHERE type='table' ORDER BY name""")
    tables = [row["name"] for row in cursor.fetchall()]

    schema = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [{"name": col["name"], "type": col["type"]}
                   for col in cursor.fetchall()
                   ]
        cursor.execute(f"SELECT COUNT(*) AS cnt FROM {table}")
        row_count = cursor.fetchone()["cnt"]
        schema.append({"table": table,"columns": columns, "row_count": row_count})

    conn.close()
    return schema