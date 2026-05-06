from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import mlflow

from backend.config import APP_NAME, APP_VERSION, MLFLOW_TRACKING_URI
from backend.models import (ChatRequest, ChatResponse, ExplainRequest, ExplainResponse)

from backend import database as db
from backend.agent import chat, explain_result, last_results

#APP setup

app = FastAPI(
    title = APP_NAME,
    version = APP_VERSION,
    description = "Natural Language to SQL - powered by Claude"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"],
    )

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.on_event("startup")
async def startup():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(APP_NAME)
    print(f"{APP_NAME} v{APP_VERSION} started")
    print(f" Docs: https://localhost:8000/docs")
    
#ROUTES
@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health():
    return{ "status": "healthy", "app": APP_NAME, "version": APP_VERSION}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """main chat route.Receives question, runs agent, returns response+SQL+results"""

    try: 
        with mlflow.start_run():
             mlflow.log_param("question", request.message[:200])
             mlflow.log_param("session_id", request.session_id)

             result = chat(user_message=request.message, session_id=request.session_id)
             mlflow.log_param("agent_action", result["agent_action"])
             mlflow.log_metric("row_count", result['row_count'])
             return ChatResponse(
                 response = result["response"],
                 sql_used = result["sql_used"],
                 columns = result["columns"],
                 rows = result["rows"],
                 row_count = result["row_count"],
                 agent_action = result["agent_action"],
                 session_id = result["session_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail= str(e))
    

@app.post("/explain", response_model = ExplainResponse)
async def explain_endpoint(request: ExplainRequest):
    """[Explain this] button route.
    Takes the last query result for this session and asks LLM (Claude) to interpret it in business terms. No Agent loop"""
    try:
        explanation = explain_result(session_id=request.session_id)
        return ExplainResponse(explanation=explanation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/schema")
async def schema_endpoint():
    """
    Returns database schema as structured JSON.
    Powers the schema explorer panel in the frontend.
    Called once when the page loads.
    """
    try:
        return db.get_schema_for_api()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def stats():
    """
    Quick stats for the UI header.
    Shows users how much data they're working with.
    """
    try:
        schema = db.get_schema_for_api()
        total_rows = sum(t["row_count"] for t in schema)
        return {
            "tables":     len(schema),
            "total_rows": total_rows,
            "database":   "Corp"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))