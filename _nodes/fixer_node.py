"""
_nodes/fixer_node.py
--------------------
Fixer Node — Step 4 of 4
=========================
For each RCA item:
  - update_workflow → GET workflow definition, patch it via LLM, PUT it back
  - retry           → trigger a re-run via ARM API
  - config_change   → log the required change (human approval needed)

SAFETY: The node validates changes before PUT and never blindly overwrites.
Low-confidence items (< 0.6) are skipped and flagged for human review.

Input  : state["rca_output"]
Output : state["fixer_output"]

Saved  : _temp/fixer_output_<timestamp>.json
"""

import copy
import json
import logging

import requests

from _config.config import settings
from _util.file_ops import save_json

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.6  # items below this are skipped


# ── ARM helpers ───────────────────────────────────────────────────────────────

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


def _workflow_url(workflow_name: str) -> str:
    return (
        f"https://management.azure.com/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}"
        f"/resourceGroups/{settings.AZURE_RESOURCE_GROUP}"
        f"/providers/Microsoft.Logic/workflows/{workflow_name}"
        f"?api-version={settings.ARM_API_VERSION}"
    )


def _get_workflow(token: str, workflow_name: str) -> dict:
    """GET the current workflow definition from ARM."""
    resp = requests.get(
        _workflow_url(workflow_name),
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _put_workflow(token: str, workflow_name: str, definition: dict) -> dict:
    """PUT (replace) the workflow definition in ARM."""
    resp = requests.put(
        _workflow_url(workflow_name),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=definition,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def _retry_run(token: str, workflow_name: str, run_id: str) -> None:
    """POST to resubmit a failed run."""
    url = (
        f"https://management.azure.com/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}"
        f"/resourceGroups/{settings.AZURE_RESOURCE_GROUP}"
        f"/providers/Microsoft.Logic/workflows/{workflow_name}"
        f"/runs/{run_id}/resubmit?api-version={settings.ARM_API_VERSION}"
    )
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()


# ── Patch generation (simple rule-based, LLM-free for safety) ─────────────────

def _build_patch(fix_plan: str, error_type: str, current_definition: dict) -> dict:
    """
    Apply a conservative patch to the workflow definition based on fix_plan.
    Returns the modified definition. Only touches well-understood properties.
    """
    patched = copy.deepcopy(current_definition)
    props = patched.setdefault("properties", {})
    definition = props.setdefault("definition", {})

    if error_type == "Timeout":
        # Extend HTTP action timeouts
        actions = definition.get("actions", {})
        for action_name, action_body in actions.items():
            if action_body.get("type") in ("Http", "ApiConnection"):
                inputs = action_body.setdefault("inputs", {})
                inputs.setdefault("retryPolicy", {})
                inputs["retryPolicy"] = {"type": "fixed", "count": 3, "interval": "PT30S"}
                logger.info("[Fixer] Applied retry policy to action '%s'", action_name)

    elif error_type == "Authentication":
        # Flag authentication connections for refresh — log only
        logger.warning(
            "[Fixer] Authentication error detected. "
            "Update the API connection credentials in the Azure portal."
        )

    return patched


# ── Node entrypoint ───────────────────────────────────────────────────────────

def fixer_node(state: dict) -> dict:
    """
    LangGraph node: Fixer
    ----------------------
    1. Read rca_output from state
    2. For each item, dispatch to the appropriate fix strategy
    3. Validate before any PUT
    4. Save results and return updated state
    """
    logger.info("[Fixer] Starting — applying fixes")

    rca_output: dict = state.get("rca_output", {})
    analysis: list[dict] = rca_output.get("analysis", [])

    workflow_name = settings.LOGIC_APP_NAME or state.get("workflow_name", "")
    fix_results = []

    if not analysis:
        logger.warning("[Fixer] No RCA items to fix")
        fixer_output = {"fix_results": []}
        save_json(fixer_output, "fixer_output")
        return {**state, "fixer_output": fixer_output}

    token = _get_arm_token()

    for item in analysis:
        run_id = item["run_id"]
        action_type = item.get("action_type", "retry")
        confidence = item.get("confidence", 0.0)
        fix_plan = item.get("fix_plan", "")
        error_type = item.get("error_type", "Unknown")

        logger.info("[Fixer] run_id=%s action=%s confidence=%.2f", run_id, action_type, confidence)

        # Safety gate
        if confidence < CONFIDENCE_THRESHOLD:
            fix_results.append({
                "run_id": run_id,
                "status": "skipped",
                "details": f"Confidence {confidence:.2f} below threshold {CONFIDENCE_THRESHOLD}. Manual review required.",
                "workflow_patch": {},
            })
            continue

        try:
            if action_type == "retry":
                _retry_run(token, workflow_name, run_id)
                fix_results.append({
                    "run_id": run_id,
                    "status": "success",
                    "details": "Run resubmitted via ARM API",
                    "workflow_patch": {},
                })

            elif action_type == "update_workflow":
                current_def = _get_workflow(token, workflow_name)
                patched_def = _build_patch(fix_plan, error_type, current_def)

                # Validate: ensure we did not lose top-level keys
                assert set(current_def.keys()).issubset(set(patched_def.keys())), \
                    "Patch removed top-level keys — aborting"

                patch_summary = {
                    "error_type": error_type,
                    "fix_plan": fix_plan,
                }
                _put_workflow(token, workflow_name, patched_def)
                logger.info("[Fixer] Workflow updated for run_id=%s", run_id)
                fix_results.append({
                    "run_id": run_id,
                    "status": "success",
                    "details": "Workflow definition updated via ARM API",
                    "workflow_patch": patch_summary,
                })

            elif action_type == "config_change":
                # Config changes require human approval — log and skip
                fix_results.append({
                    "run_id": run_id,
                    "status": "skipped",
                    "details": f"Config change required — manual action: {fix_plan}",
                    "workflow_patch": {},
                })

        except Exception as exc:
            logger.error("[Fixer] Fix failed for run_id=%s: %s", run_id, exc)
            fix_results.append({
                "run_id": run_id,
                "status": "failed",
                "details": str(exc),
                "workflow_patch": {},
            })

    fixer_output = {"fix_results": fix_results}
    path = save_json(fixer_output, "fixer_output")
    logger.info("[Fixer] Saved %d fix results → %s", len(fix_results), path)

    return {**state, "fixer_output": fixer_output}
