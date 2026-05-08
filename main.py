"""
main.py
-------
FastAPI application exposing the auto-remediation pipeline as REST endpoints.

Start the server
----------------
    uvicorn main:app --reload --port 8000

Endpoints
---------
  POST /run                    — run the full pipeline (observer → classifier → rca → fixer)
  GET  /observer               — fetch & return raw failed run logs only
  GET  /workflow/{name}        — fetch a workflow definition from ARM
  PUT  /workflow/{name}        — update a workflow definition in ARM
  GET  /health                 — health / config check
"""

import json
import logging
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from _config.config import settings
from _util.file_ops import load_latest_json
from graph import build_graph
from _dashboard.dashboard_routes import router as dashboard_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Azure Logic App Auto-Remediation",
    description="LangGraph-powered pipeline: Observer → Classifier → RCA → Fixer",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(dashboard_router, prefix="/api")


# ── Shared ARM auth ───────────────────────────────────────────────────────────

def _get_arm_token() -> str:
    url = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": settings.AZURE_CLIENT_ID,
        "client_secret": settings.AZURE_CLIENT_SECRET,
        "resource": "https://management.azure.com/",
    }
    resp = requests.post(url, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def _workflow_url(name: str) -> str:
    return (
        f"https://management.azure.com/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}"
        f"/resourceGroups/{settings.AZURE_RESOURCE_GROUP}"
        f"/providers/Microsoft.Logic/workflows/{name}"
        f"?api-version={settings.ARM_API_VERSION}"
    )


# ── Request / Response models ─────────────────────────────────────────────────

class RunPipelineRequest(BaseModel):
    workflow_name: str = ""


class WorkflowUpdateRequest(BaseModel):
    definition: dict


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Utility"])
def health_check():
    """
    Health check — verifies that required environment variables are set.

    Command:
        curl http://localhost:8000/health
    """
    missing = settings.validate()
    return {
        "status": "ok" if not missing else "degraded",
        "missing_env_vars": missing,
        "logic_app": settings.LOGIC_APP_NAME or "(not set)",
    }


@app.post("/run", tags=["Pipeline"])
def run_pipeline(body: RunPipelineRequest = RunPipelineRequest()):
    """
    Run the full auto-remediation pipeline:
      Observer → Classifier → RCA → Fixer

    Each node persists its output to _temp/.

    Command:
        curl -X POST http://localhost:8000/run
        curl -X POST http://localhost:8000/run -H "Content-Type: application/json" \\
             -d '{"workflow_name": "my-logic-app"}'
    """
    initial_state: dict = {}
    if body.workflow_name:
        initial_state["workflow_name"] = body.workflow_name

    try:
        graph = build_graph()
        result = graph.invoke(initial_state)
        return {
            "status": "completed",
            "observer":   result.get("observer_output"),
            "classifier": result.get("classifier_output"),
            "rca":        result.get("rca_output"),
            "fixer":      result.get("fixer_output"),
        }
    except Exception as exc:
        logger.exception("[/run] Pipeline failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/observer", tags=["Pipeline"])
def run_observer_only(workflow_name: str = ""):
    """
    Run the Observer node in isolation — returns raw failed run logs.

    Command:
        curl "http://localhost:8000/observer?workflow_name=my-logic-app"
    """
    from _nodes.observer_node import observer_node

    state: dict = {}
    if workflow_name:
        state["workflow_name"] = workflow_name

    try:
        result = observer_node(state)
        return result.get("observer_output", {})
    except Exception as exc:
        logger.exception("[/observer] Failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/workflow/{name}", tags=["Azure ARM"])
def get_workflow(name: str):
    """
    Fetch a Logic App workflow definition from Azure ARM.

    Command:
        curl http://localhost:8000/workflow/my-logic-app
    """
    try:
        token = _get_arm_token()
        resp = requests.get(
            _workflow_url(name),
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.put("/workflow/{name}", tags=["Azure ARM"])
def update_workflow(name: str, body: WorkflowUpdateRequest):
    """
    Push an updated workflow definition to Azure ARM.
    body.definition must be the FULL ARM payload:
      { "location": "...", "properties": { "definition": {...}, "parameters": {...} } }

    Command:
        curl -X PUT http://localhost:8000/workflow/my-logic-app \\
             -H "Content-Type: application/json" \\
             -d @_temp/fixed_workflow_<timestamp>.json
    """
    if "location" not in body.definition or "definition" not in body.definition.get("properties", {}):
        raise HTTPException(
            status_code=422,
            detail="Body must include 'location' and 'properties.definition'. "
                   "Send the full ARM payload, not just the definition block.",
        )
    try:
        token = _get_arm_token()
        resp = requests.put(
            _workflow_url(name),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=body.definition,
            timeout=60,
        )
        resp.raise_for_status()
        return {"status": "updated", "workflow": name, "response": resp.json()}
    except requests.HTTPError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.put("/update-workflow", tags=["Azure ARM"])
def update_workflow_from_temp(workflow_name: str = ""):
    """
    Load the latest fixed_workflow from _temp/ and PUT it to Azure ARM.
    This lets you re-push the last fixer output without re-running the pipeline.

    Steps performed:
      1. Load _temp/fixed_workflow_<latest>.json
      2. Validate location + properties.definition are present
      3. GET current workflow from ARM to confirm it exists
      4. PUT the fixed workflow

    Command:
        curl -X PUT "http://localhost:8000/update-workflow?workflow_name=my-logic-app"
    """
    name = workflow_name or settings.LOGIC_APP_NAME
    if not name:
        raise HTTPException(status_code=422, detail="Provide workflow_name or set LOGIC_APP_NAME env var")

    try:
        fixed_workflow = load_latest_json("fixed_workflow")
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="No fixed_workflow file found in _temp/. Run the pipeline first (POST /run).",
        )

    # Validate structure before touching Azure
    if "location" not in fixed_workflow:
        raise HTTPException(status_code=422, detail="fixed_workflow is missing 'location'")
    if "definition" not in fixed_workflow.get("properties", {}):
        raise HTTPException(status_code=422, detail="fixed_workflow is missing 'properties.definition'")
    if "$connections" not in fixed_workflow.get("properties", {}).get("parameters", {}):
        logger.warning("[/update-workflow] No $connections in parameters — workflow may use connectors that will break")

    try:
        token = _get_arm_token()
        resp = requests.put(
            _workflow_url(name),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=fixed_workflow,
            timeout=60,
        )
        resp.raise_for_status()
        logger.info("[/update-workflow] Workflow '%s' updated successfully", name)
        return {
            "status": "updated",
            "workflow": name,
            "response": resp.json(),
        }
    except requests.HTTPError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except Exception as exc:
        logger.exception("[/update-workflow] Failed")
        raise HTTPException(status_code=500, detail=str(exc))
