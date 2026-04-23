# backend/agent.py
import json
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage


from backend.config import ANTHROPIC_API_KEY
from backend import governance_db as db

# TOOL 1: Search Assets

@tool
def search_assets(query:str) -> str:
    """
    Search for data assets in the governance catalogue by name, 
    description, or domain. Use this when the user mentions a 
    specific table, dataset, report, or domain name. 
    Returns a list of matching assets with their metadata.
    Input: a search term like 'customer', 'finance', or 'transactions'
    """
    results = db.search_assets(query)
    if not results:
        return f" No Assets found matching to the criteria '{query}'."
    output = f"Found {len(results)} asset(s) matching '{query}': \n\n"

    for a in results:
        output += (
            f" ID {a['id']}: {a['name']} ({a['asset_type']}) \n"
            f" Domain: {a['domain'] or 'unset'} | "
            f"Owner: {a['owner'] or 'UNOWNED'}"
            f"Sensitivity:{a['owner'] or 'unset'} \n"
            f"Description: {a['description'] or 'none'}\n"
            f" Tags:{','.join(a['tags']) if a['tags'] else 'none'}\n\n"
        )
    return output

@tool
def list_all_assets(domain: str = "") -> str:
    """
    List all data assets in the governance catalogue, optionally 
    filtered by domain. Use this when the user wants an overview 
    of all assets or all assets in a specific domain.
    Input: domain name like 'finance', 'hr', 'sales', 'operations' 
    or empty string for all assets.
    """

    if domain:
        assets = db.get_assets_by_domain(domain)
        header = f"Assets in the '{domain}' domain:\n\n"
    else:
        assets = db.get_all_assets()
        header = f"All assets in the governance catalogue. \n\n"

    if not assets:
        return f"No assets found{'in domain:' + domain if domain else ''}."
    
    output = header
    for a in assets:
        output += (
            f" ID {a['id']}: {a['name']} ({a['asset_type']}) |"
            f"Owner: {a['owner'] or 'UNOWNED'} |"
            f"Sensitivity: {a['sensitivity'] or 'unset'}\n"
        )
    return output
    
@tool
def classify_asset(asset_id: int, domain:str, sensitivity: str, tags: str, reasoning: str ) -> str:
    """
    Classify a data asset by assigning it a domain, sensitivity level, 
    and tags. Use this when the user asks to classify a dataset or 
    when an asset has missing domain or sensitivity information.
    
    sensitivity must be one of: public, internal, confidential, restricted
    domain must be one of: finance, hr, sales, operations, marketing, legal, other
    tags should be a comma-separated string like 'pii,financial,raw'
    reasoning: explain why you chose this classification
    """
    # Validate sensitivity
    valid_sensitivity = ["public","internal","confidential","restricted"]
    if sensitivity.lower() not in valid_sensitivity:
        return f"invalid sensitivity '{sensitivity}'. Must be one of : {valid_sensitivity}"
    
    #Convert comma-seperated tags string to list
    tags_list = [t.strip() for t in tags.split(",") if t.strip()]

    #update the asset in the database
    success = db.update_asset(
        asset_id,domain = domain.lower(), sensitivity=sensitivity.lower(), tags = json.dumps(tags_list)
    )
    return f"Successfully updated!"
# TOOL 4: Generate Data Quality Rule

@tool
def generate_quality_rule(asset_id: int, column_name: str, rule_type: str, rule_definition: str, sql_expression: str) -> str:
    """
    Generate and save a data quality rule for a specific column 
    in a data asset. Use this when the user asks to create data 
    quality rules, validation checks, or DQ rules for a column.
    
    rule_type must be one of: not_null, format, range, uniqueness, referential
    rule_definition: human-readable description of the rule
    sql_expression: the actual SQL check expression, e.g. "email LIKE '%@%.%'"
    """
   
    
    valid_types = ["not_null","format","range","uniqueness","referential"]
    if rule_type.lower() not in valid_types:
        return f" Invalid rule_type '{rule_type}'. Must be one of: {valid_types}"
    
    asset = db.get_asset_by_id(asset_id)
    if not asset:
        return f"Asset ID {asset_id} not found."
    
    rule_id = db.add_quality_rule(
        asset_id = asset_id,
        column_name = column_name,
        rule_type = rule_type.lower(),
        rule_definition = rule_definition,
        sql_expression = sql_expression
    )

    return (
        f"Quality rule created (ID: {rule_id}) for '{asset['name']}.{column_name}':\n"
        f"  Type: {rule_type}\n"
        f"  Rule: {rule_definition}\n"
        f"  SQL: {sql_expression}"
    )
@tool
def suggest_ownership(asset_id: int, suggested_owner: str, reasoning: str) -> str:
    """
    Suggest and assign an owner to a data asset that currently has 
    no owner. Use this when the user asks who should own an asset,
    or when listing unowned assets and recommending owners.
    suggested_owner: email or team name of the recommended owner
    reasoning: why this owner makes sense for this asset
    """
    asset = db.get_asset_by_id(asset_id)
    if not asset:
        return f"Asset ID{asset_id} not found."
    db.update_asset(asset_id, owner=suggested_owner)
    return (
        f"✅ Ownership assigned for '{asset['name']}':\n"
        f"  Owner: {suggested_owner}\n"
        f"  Reasoning: {reasoning}"
    )

@tool
def explain_lineage(asset_id: int) ->str:
    """Explain the data lineage for a specific asset.Use this 
    when a user asks about lineage, data flow, data origin, 
    dependencies, or impact analysis for a dataset.
"""

    asset = db.get_asset_by_id(asset_id)
    if not asset:
        return f"Asset ID {asset_id} not found"
    
    lineage = db.get_lineage_for_asset(asset_id)
    upstream = lineage["upstream"]
    downstream = lineage["downstream"]
    output = f" Lineage for '{asset['name']}' (ID: {asset_id}):\n\n"

    if upstream:
        output += "UPSTREAM (this asset is built from):\n"
        for u in upstream:
            output += f"{u['name']} ({u['asset_type']}) [{u['relationship']}]\n"
    else:
        output += "UPSTREAM: None = this is a source asset. \n"
    output +="\n"
    if downstream:
        output += "downstream (this asset feeds into):\n"
        for d in downstream:
            output += f"{d['name']} ({d['asset_type']}) [{d['relationship']}] \n"
    else:
        output += "⬇️  DOWNSTREAM: None — this is an endpoint asset.\n"        
    return output


@tool
def governance_report(report_type: str) -> str:
    """
    Generate a governance health report. Use this when the user 
    asks for a report, overview, health check, or summary of the 
    data catalogue.
    
    report_type must be one of:
    - 'unowned': lists all assets with no owner assigned
    - 'full': complete catalogue summary with stats
    """
    if report_type == "unowned":
        assets = db.get_unowned_assets()
        if not assets:
            return "✅ All assets have owners assigned. Governance health: GOOD."
        output = f"⚠️  {len(assets)} asset(s) with no owner assigned:\n\n"
        for a in assets:
            output += (
                f"• ID {a['id']}: {a['name']} ({a['asset_type']}) "
                f"| Domain: {a['domain'] or 'unset'} "
                f"| Sensitivity: {a['sensitivity'] or 'unset'}\n"
            )
        return output

    elif report_type == "full":
        all_assets = db.get_all_assets()
        unowned = db.get_unowned_assets()
        domains = {}
        for a in all_assets:
            d = a["domain"] or "unset"
            domains[d] = domains.get(d, 0) + 1

        output = "📋 GOVERNANCE HEALTH REPORT\n"
        output += "=" * 40 + "\n\n"
        output += f"Total assets:     {len(all_assets)}\n"
        output += f"Unowned assets:   {len(unowned)} "
        output += ("✅" if not unowned else "⚠️") + "\n\n"
        output += "Assets by domain:\n"
        for domain, count in sorted(domains.items()):
            output += f"  • {domain}: {count}\n"
        return output

    else:
        return f"Unknown report type '{report_type}'. Use 'unowned' or 'full'."

SYSTEM_PROMPT = """You are GovernanceGPT, an expert AI Data Governance Copilot
built for enterprise data teams. You help data stewards, data owners, and
governance teams manage their data catalogue efficiently.

You have access to a live governance database containing data assets,
lineage relationships, quality rules, and audit logs.

YOUR CAPABILITIES:
- Search and retrieve data assets from the catalogue
- Classify assets with domain, sensitivity, and tags
- Generate data quality rules for specific columns
- Suggest ownership for unowned assets
- Explain data lineage (upstream and downstream)
- Generate governance health reports

YOUR BEHAVIOUR:
- Always search the database before answering questions about specific assets
- When classifying, be specific about WHY you chose a sensitivity level
- When suggesting ownership, look at the domain and existing owners for context
- Be concise but thorough — data teams are busy people
- If you're unsure about something, say so rather than guessing
- Always confirm when you've made a change to the database

SENSITIVITY LEVELS (in order of restrictiveness):
- public: freely shareable, no personal data
- internal: for employees only, no PII
- confidential: sensitive business or customer data, limited access
- restricted: highest sensitivity (PII, financial, legal), strict controls

You are the expert. Be decisive and professional."""

# All tools in one list
TOOLS = [
    search_assets,
    list_all_assets,
    classify_asset,
    generate_quality_rule,
    suggest_ownership,
    explain_lineage,
    governance_report
]

def create_agent():
   
    llm = ChatAnthropic(
        model="claude-sonnet-4-5",
        api_key=ANTHROPIC_API_KEY,
        temperature=0,
        max_tokens=2000
    )
    return create_react_agent(llm, TOOLS, prompt=SYSTEM_PROMPT)


# Store conversation history per session
chat_histories = {}

def chat(user_message: str, session_id: str = "default") -> dict:
    """Main entry point. Takes a user message, runs the agent, logs the result to the audit log, and returns a response."""
    agent = create_agent()

    #Get or create chat history for this session
    history = chat_histories.get(session_id, [])
    
    #Run the agent — LangGraph expects messages list (history + new message)
    result = agent.invoke({"messages": history + [HumanMessage(content=user_message)]})
    response_text = result["messages"][-1].content
    
    # Update conversation history
    history.append(HumanMessage(content=user_message))
    history.append(AIMessage(content=response_text))
    chat_histories[session_id] = history

    agent_action = "general_purpose"
    assets_touched = []

    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                agent_action = tc["name"]
                if isinstance(tc.get("args"), dict) and "asset_id" in tc["args"]:
                    assets_touched.append(tc["args"]["asset_id"])

    # Log everything to the audit trail
    db.log_audit(
        user_query=user_message,
        agent_action=agent_action,
        assets_touched=assets_touched,
        result_summary=response_text[:200],
        full_response=response_text
    )

    return {
        "response": response_text,
        "agent_action": agent_action,
        "assets_touched": assets_touched,
        "session_id": session_id
    }

