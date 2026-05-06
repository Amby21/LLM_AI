import re

#words that should never be in the SQL 
DANGEROUS_WORDS = ["DELETE","DROP","UPDATE","INSERT","TRUNCATE","ALTER","CREATE","GRANT","REVOKE","EXEC","EXECUTE","MERGE","REPLACE","ATTACH","DETACH"]

def validate_sql(sql:str) ->dict:
    """
    Runs 3 safety checks on a SQL string. Returns {"safe": True/False,"reason":"why it failed"}
    Called by the agent's run_query tool before every execution
    """

    if not sql or not sql.strip():
        return {"safe": False,"reason": "Empty SQL query"}
    #normalize: remove extra whitespace , uppercase for comparison

    sql_clean = sql.strip()
    sql_upper = sql_clean.upper()

    # CHECK 1: Must start with select, as SELECT can only read-never modify.
    # Delete leading comments before the SQL statement.
    sql_no_comments = re.sub(r'/\*.*?\*/','', sql_upper, flags = re.DOTALL)
    sql_no_comments = re.sub(r'--.*$','',sql_no_comments, flags = re.MULTILINE)
    sql_stripped = sql_no_comments.strip()

    if not sql_stripped.startswith("SELECT") and not sql_stripped.startswith("WITH"):
        return {"safe": False,
                "reason":(f"Query must start with SELECT or WITH."
                          f"Got:'{sql_clean[:50]}...'"
                          f"DataDialogue is read-only and cannot modify data.")}
    
    #CHECK 2 : Dangerous keyword scan
    # SELECT * FROM users ; DELETE FROM users
    for keyword in DANGEROUS_WORDS:
        pattern = rf'\b{keyword}\b'
        if re.search(pattern, sql_upper):
            return{"safe": False, "reason": (f"Query contains forbidden keyword:'{keyword}" f"DataDialogue is read-only.")}

    sql_no_strings = re.sub(r"'[^']*'","''", sql_clean)
    sql_no_strings = re.sub(r"'[^']*'","''", sql_no_strings)
    semicolons     = sql_no_strings.count(';')
    if semicolons > 1:

        return {"safe": False, "reason":(f"Query contains multiple statements ({semicolons} semicolons)."
                                         f"Only single SELECT statements are allowed.")}
    
    return {"safe": True,"reason":"Query passed all safety checks"}

def sanitise_sql(sql: str) -> str:
    """Light cleanup of SQL before validation. Removes leading/trailing whitespace and normalises line breaks. Does NOT modify the SQL logic"""
    return " ".join(sql.split())

