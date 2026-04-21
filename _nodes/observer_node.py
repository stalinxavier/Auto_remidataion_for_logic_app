"""
_nodes/observer_node.py
-----------------------
Observer Node — Step 1 of 4
============================
Fetches failed Logic App run errors from Azure ARM API and
Log Analytics, then serialises them to _temp/observer_output.json.

Input  : LangGraph state dict (may be empty at start)
Output : state dict with key "observer_output"

Saved  : _temp/observer_<timestamp>.json
"""

import logging
from datetime import datetime, timedelta, timezone

import requests

from _config.config import settings
from _util.file_ops import save_json

logger = logging.getLogger(__name__)

# ── Azure ARM helpers ─────────────────────────────────────────────────────────

def _get_arm_token() -> str:
    """Obtain a bearer token for Azure Resource Manager."""
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


def _list_failed_runs(token: str, workflow_name: str) -> list[dict]:
    """
    GET /subscriptions/.../runs?$filter=status eq 'Failed'
    Returns raw ARM run objects.
    """
    base = (
        f"https://management.azure.com/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}"
        f"/resourceGroups/{settings.AZURE_RESOURCE_GROUP}"
        f"/providers/Microsoft.Logic/workflows/{workflow_name}/runs"
    )
    params = {
        "api-version": settings.ARM_API_VERSION,
        "$filter": "status eq 'Failed'",
        "$top": "50",
    }
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(base, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("value", [])


def _extract_error(run: dict) -> dict:
    """Pull the fields we care about from an ARM run object."""
    props = run.get("properties", {})
    error = props.get("error", {})
    return {
        "run_id": run.get("name", "unknown"),
        "workflow_id": props.get("workflow", {}).get("name", settings.LOGIC_APP_NAME),
        "error_message": error.get("message", "No error message"),
        "error_code": error.get("code", ""),
        "status": props.get("status", ""),
        "start_time": props.get("startTime", ""),
        "end_time": props.get("endTime", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Node entrypoint ───────────────────────────────────────────────────────────

def observer_node(state: dict) -> dict:
    """
    LangGraph node: Observer
    ------------------------
    1. Authenticate against Azure ARM
    2. List failed runs for the configured Logic App
    3. Extract error details
    4. Save to _temp and return updated state
    """
    logger.info("[Observer] Starting — fetching failed Logic App runs")

    workflow_name = settings.LOGIC_APP_NAME or state.get("workflow_name", "")
    if not workflow_name:
        raise ValueError("LOGIC_APP_NAME env var or state['workflow_name'] is required")

    token = _get_arm_token()
    raw_runs = _list_failed_runs(token, workflow_name)

    errors = [_extract_error(r) for r in raw_runs]

    observer_output = {
        "workflow_id": workflow_name,
        "total_failed": len(errors),
        "errors": errors,
    }

    path = save_json(observer_output, "observer_output")
    logger.info("[Observer] Saved %d failed runs → %s", len(errors), path)

    return {**state, "observer_output": observer_output}
