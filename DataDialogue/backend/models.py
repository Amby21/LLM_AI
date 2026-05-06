from pydantic import BaseModel
from typing import Optional, List, Any

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    sql_used: Optional[str]
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    agent_action: str = "general_response"
    session_id: str

class ExplainRequest(BaseModel):
    """Sent when user clicks [Explain this] button"""
    session_id: str

class ExplainResponse(BaseModel):
    """Business Interpretation of the last result"""
    explanation: str

# curl -X POST http://localhost:8000/chat \
#     -H "Content-Type: application/json" \
#     -d '{"message": "who are our top 5 customers by revenue?", "session_id": "test"}'