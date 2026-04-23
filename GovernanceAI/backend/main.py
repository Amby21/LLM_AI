# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import mlflow
import os

from backend.config import APP_NAME, APP_VERSION, MLFLOW_TRACKING_URI
from backend.models import ChatRequest, ChatResponse, AssetCreate
from backend import governance_db as db
from backend.agent import chat

# ─── APP SETUP ────────────────────────────────────────────────────────

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered Data Governance Copilot"
)


# In production, replace with domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend HTML file at /
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialise database on startup
@app.on_event("startup")
async def startup():
    db.initialise_database()
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(APP_NAME)
    print(f"✅ {APP_NAME} v{APP_VERSION} started")


# ─── ROUTES ───────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Serve the frontend UI"""
    return FileResponse("frontend/index.html")


@app.get("/health")
async def health():
    """Health check — useful for Docker and deployment monitoring"""
    return {"status": "healthy", "app": APP_NAME, "version": APP_VERSION}


# ─── CHAT ─────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint. Receives a user message, runs the agent,
    logs to MLFlow, and returns the response.
    """
    try:
        # Log to MLFlow — every chat is an experiment run
        with mlflow.start_run():
            mlflow.log_param("user_query", request.message[:200])
            mlflow.log_param("session_id", request.session_id)

            result = chat(
                user_message=request.message,
                session_id=request.session_id
            )

            mlflow.log_param("agent_action", result["agent_action"])
            mlflow.log_metric("assets_touched_count",
                              len(result["assets_touched"]))
            mlflow.log_param("response_preview", result["response"][:200])

        return ChatResponse(
            response=result["response"],
            agent_action=result["agent_action"],
            assets_touched=result["assets_touched"],
            session_id=result["session_id"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── ASSETS ───────────────────────────────────────────────────────────

@app.get("/assets")
async def get_assets(domain: str = ""):
    """
    Returns all assets, optionally filtered by domain.
    """
    if domain:
        return db.get_assets_by_domain(domain)
    return db.get_all_assets()


@app.get("/assets/{asset_id}")
async def get_asset(asset_id: int):
    """Returns a single asset by ID. Example: GET /assets/6"""
    asset = db.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    return asset


@app.post("/assets")
async def create_asset(asset: AssetCreate):
    """Creates a new asset in the catalogue."""
    asset_id = db.create_asset(
        name=asset.name,
        asset_type=asset.asset_type,
        domain=asset.domain,
        owner=asset.owner,
        sensitivity=asset.sensitivity,
        description=asset.description,
        tags=asset.tags
    )
    return {"id": asset_id, "message": f"Asset '{asset.name}' created"}


@app.get("/assets/{asset_id}/lineage")
async def get_lineage(asset_id: int):
    """Returns upstream + downstream lineage for an asset."""
    asset = db.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    lineage = db.get_lineage_for_asset(asset_id)
    return {"asset": asset, "lineage": lineage}


@app.get("/assets/{asset_id}/rules")
async def get_quality_rules(asset_id: int):
    """Returns all data quality rules for an asset."""
    return db.get_rules_for_asset(asset_id)


# ─── GOVERNANCE ───────────────────────────────────────────────────────

@app.get("/governance/unowned")
async def get_unowned():
    """Returns all assets with no owner — key governance health metric."""
    return db.get_unowned_assets()


@app.get("/governance/audit")
async def get_audit_log(limit: int = 50):
    """
    Returns the audit log — every action the agent has ever taken.
    Example: GET /governance/audit?limit=20
    """
    return db.get_audit_log(limit)


@app.get("/governance/stats")
async def get_stats():
    """Returns summary statistics for the governance dashboard."""
    all_assets = db.get_all_assets()
    unowned = db.get_unowned_assets()
    audit = db.get_audit_log(limit=100)

    # Count by domain
    domains = {}
    sensitivity_counts = {}
    for a in all_assets:
        d = a["domain"] or "unset"
        s = a["sensitivity"] or "unset"
        domains[d] = domains.get(d, 0) + 1
        sensitivity_counts[s] = sensitivity_counts.get(s, 0) + 1

    return {
        "total_assets": len(all_assets),
        "unowned_count": len(unowned),
        "total_agent_actions": len(audit),
        "assets_by_domain": domains,
        "assets_by_sensitivity": sensitivity_counts,
    }