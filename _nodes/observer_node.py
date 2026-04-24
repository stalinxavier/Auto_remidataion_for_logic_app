"""
_nodes/observer_node.py
-----------------------
Observer Node — Step 1 of 4
============================
Fetches TWO things from Azure ARM in a single authenticated session:
  1. Failed Logic App run errors (last 50 failures)
  2. The current workflow definition JSON

Having the workflow definition available from step 1 means the RCA node can
reference real action names and the Fixer node avoids a redundant GET call.

Input  : LangGraph state dict (empty at pipeline start)
Output : state dict with keys:
           "observer_output"      — errors + metadata
           "workflow_definition"  — raw ARM workflow object

Saved  : _temp/observer_output_<timestamp>.json
"""

import logging
from datetime import datetime, timezone

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


def _get_workflow_definition(token: str, workflow_name: str) -> dict:
    """
    GET /subscriptions/.../workflows/{name}
    Returns the full ARM workflow object including the definition JSON.
    """
    url = (
        f"https://management.azure.com/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}"
        f"/resourceGroups/{settings.AZURE_RESOURCE_GROUP}"
        f"/providers/Microsoft.Logic/workflows/{workflow_name}"
        f"?api-version={settings.ARM_API_VERSION}"
    )
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _list_failed_runs(token: str, workflow_name: str) -> list[dict]:
    """
    GET /subscriptions/.../workflows/{name}/runs?$filter=status eq 'Failed'
    Returns the last 50 failed run objects.
    """
    url = (
        f"https://management.azure.com/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}"
        f"/resourceGroups/{settings.AZURE_RESOURCE_GROUP}"
        f"/providers/Microsoft.Logic/workflows/{workflow_name}/runs"
    )
    params = {
        "api-version": settings.ARM_API_VERSION,
        "$filter": "status eq 'Failed'",
        "$top": "50",
    }
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("value", [])


def _get_failed_actions(token: str, workflow_name: str, run_id: str) -> list[dict]:
    """
    GET /runs/{runId}/actions  — fetch action-level detail for a failed run.
    Returns a trimmed list of failed actions (name, status, error).
    """
    url = (
        f"https://management.azure.com/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}"
        f"/resourceGroups/{settings.AZURE_RESOURCE_GROUP}"
        f"/providers/Microsoft.Logic/workflows/{workflow_name}"
        f"/runs/{run_id}/actions?api-version={settings.ARM_API_VERSION}"
    )
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    if not resp.ok:
        return []
    actions = resp.json().get("value", [])
    failed = []
    for a in actions:
        props = a.get("properties", {})
        if props.get("status") == "Failed":
            failed.append({
                "action_name": a.get("name", ""),
                "status_code": props.get("code", ""),
                "error_message": props.get("error", {}).get("message", ""),
                "start_time": props.get("startTime", ""),
            })
    return failed


def _extract_error(token: str, workflow_name: str, run: dict) -> dict:
    """Pull error fields from an ARM run object and enrich with action details."""
    props = run.get("properties", {})
    error = props.get("error", {})
    run_id = run.get("name", "unknown")

    failed_actions = _get_failed_actions(token, workflow_name, run_id)

    return {
        "run_id": run_id,
        "error_message": error.get("message", "No error message"),
        "error_code": error.get("code", ""),
        "status": props.get("status", ""),
        "start_time": props.get("startTime", ""),
        "end_time": props.get("endTime", ""),
        "failed_actions": failed_actions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Node entrypoint ───────────────────────────────────────────────────────────

def observer_node(state: dict) -> dict:
    """
    LangGraph node: Observer
    ------------------------
    1. Authenticate against Azure ARM (single token for all calls)
    2. Download the current workflow definition
    3. List failed runs and enrich each with action-level errors
    4. Save combined output to _temp and return updated state

    State keys produced
    -------------------
    observer_output     : { workflow_id, total_failed, errors[] }
    workflow_definition : raw ARM workflow object (passed to Fixer without re-fetching)
    """
    logger.info("[Observer] Starting — fetching workflow definition + failed runs")

    workflow_name = settings.LOGIC_APP_NAME or state.get("workflow_name", "")
    if not workflow_name:
        raise ValueError("LOGIC_APP_NAME env var or state['workflow_name'] is required")

    token = _get_arm_token()

    # ── 1. Download workflow definition ──────────────────────────────────────
    logger.info("[Observer] Downloading workflow definition for '%s'", workflow_name)
    workflow_definition = _get_workflow_definition(token, workflow_name)

    action_names = list(
        workflow_definition.get("properties", {})
        .get("definition", {})
        .get("actions", {})
        .keys()
    )
    logger.info("[Observer] Workflow has %d actions: %s", len(action_names), action_names)

    # ── 2. Fetch failed runs with action detail ───────────────────────────────
    raw_runs = _list_failed_runs(token, workflow_name)
    errors = [_extract_error(token, workflow_name, r) for r in raw_runs]

    observer_output = {
        "workflow_id": workflow_name,
        "total_failed": len(errors),
        "workflow_action_names": action_names,
        "errors": errors,
    }

    path = save_json(observer_output, "observer_output")
    logger.info("[Observer] %d failed runs, workflow definition downloaded → %s", len(errors), path)

    return {
        **state,
        "observer_output": observer_output,
        "workflow_definition": workflow_definition,
    }
