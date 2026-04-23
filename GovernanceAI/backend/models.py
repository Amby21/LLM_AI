# backend /model.py
from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    """What the frontend sends to /chat"""
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    """What /chat sends back to the frontend"""
    response:str
    agent_action: str
    assets_touched: List[int] = []
    session_id: str

class AssetCreate(BaseModel):
    """Shape of data needed to create a new asset via API"""
    name: str
    asset_type: str
    domain: Optional[str] = None
    owner: Optional[str] = None
    sensitivity: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]]  = []

class AssetResponse(BaseModel):
    """Shape of asset data returned by the API"""
    id: int
    name: str
    asset_type: str
    domain: Optional[str]
    owner: Optional[str]
    sensitivity: Optional[str]
    description: Optional[str]
    tags: List[str] = []
    created_at: str
    updated_at: str

class AuditEntry(BaseModel):
    """Shape of an audit log entry"""
    id: int
    user_query: str
    agent_action: str
    assets_touched: str
    result_summary: Optional[str]
    timestamp: str

