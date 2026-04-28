"""
_nodes/fixer_node.py
--------------------
Fixer Node — Step 4 of 4
=========================
Uses the workflow definition already downloaded by the Observer node.
No redundant GET call is made.

For each RCA item the node dispatches to one of three strategies:

  update_workflow
    1. Ask the LLM for surgical ActionPatch instructions
       (action name + dot-path + new value) — NOT a full rewrite
    2. Apply each patch programmatically via _apply_patch()
    3. Validate structural integrity
    4. PUT the patched definition back to Azure ARM

  retry
    POST to the ARM resubmit endpoint for the failed run.

  config_change
    Flagged for human review — never automated.

SAFETY RULES
------------
  - Items with confidence < CONFIDENCE_THRESHOLD are skipped.
  - Patches are applied one-by-one; a bad path raises KeyError and is caught.
  - Structural validation (no top-level key removal) runs before every PUT.

Input  : state["rca_output"]  +  state["workflow_definition"]
Output : state["fixer_output"]

Saved  : _temp/fixer_output_<timestamp>.json
         _temp/patched_workflow_<timestamp>.json  (for update_workflow items)
"""

import copy
import json
import logging
from functools import reduce

import requests

from _config.config import settings
from _llm.factory_llm import get_llm, call_llm_structured
from _llm.models_llm import WorkflowFixInstruction
from _util.file_ops import save_json

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.6


# ── ARM helpers ───────────────────────────────────────────────────────────────

def _get_arm_token() -> str:
    url = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/token"
    resp = requests.post(
        url,
        data={
            "grant_type": "client_credentials",
            "client_id": settings.AZURE_CLIENT_ID,
            "client_secret": settings.AZURE_CLIENT_SECRET,
            "resource": "https://management.azure.com/",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _workflow_url(name: str) -> str:
    return (
        f"https://management.azure.com/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}"
        f"/resourceGroups/{settings.AZURE_RESOURCE_GROUP}"
        f"/providers/Microsoft.Logic/workflows/{name}"
        f"?api-version={settings.ARM_API_VERSION}"
    )


def _build_put_body(full_workflow: dict, updated_definition: dict) -> dict:
    """
    Build the ARM PUT body preserving location, parameters ($connections), and
    any other properties — only swapping in the updated definition block.
    """
    original_props = full_workflow.get("properties", {})
    return {
        "location": full_workflow.get("location", ""),
        "properties": {
            **original_props,           # keeps parameters.$connections and everything else
            "definition": updated_definition,
        },
    }


def _validate_put_body(body: dict) -> None:
    """Raise if the PUT body is missing fields Azure requires."""
    if not body.get("location"):
        raise ValueError("PUT body is missing 'location' — Azure will reject this request")
    props = body.get("properties", {})
    if "definition" not in props:
        raise ValueError("PUT body is missing 'properties.definition' — Azure will reject this request")


def _put_workflow(token: str, workflow_name: str, full_workflow: dict, updated_definition: dict) -> dict:
    """PUT the patched workflow back to Azure ARM."""
    body = _build_put_body(full_workflow, updated_definition)
    _validate_put_body(body)
    resp = requests.put(
        _workflow_url(workflow_name),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def _retry_run(token: str, workflow_name: str, run_id: str) -> None:
    """POST to the ARM resubmit endpoint to re-trigger a failed run."""
    url = (
        f"https://management.azure.com/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}"
        f"/resourceGroups/{settings.AZURE_RESOURCE_GROUP}"
        f"/providers/Microsoft.Logic/workflows/{workflow_name}"
        f"/runs/{run_id}/resubmit?api-version={settings.ARM_API_VERSION}"
    )
    resp = requests.post(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    resp.raise_for_status()


# ── Surgical patch application ────────────────────────────────────────────────

def _set_nested(obj: dict, path: str, value) -> None:
    """
    Set obj[part1][part2]...[partN] = value using a dot-separated path.
    Creates intermediate dicts if they don't exist.
    Raises KeyError if the first key (action_name level) does not exist.
    """
    parts = path.split(".")
    target = obj
    for part in parts[:-1]:
        if part not in target:
            target[part] = {}
        target = target[part]
    target[parts[-1]] = value


def _apply_patch(definition: dict, action_name: str, property_path: str, new_value) -> dict:
    """
    Apply a single ActionPatch to a deep-copy of the workflow *definition* block.
    Raises KeyError if action_name does not exist in definition["actions"].
    """
    patched = copy.deepcopy(definition)
    actions = patched.get("actions", {})
    if action_name not in actions:
        raise KeyError(
            f"Action '{action_name}' not found in workflow. "
            f"Available: {list(actions.keys())}"
        )
    try:
        parsed_value = json.loads(new_value)
    except (json.JSONDecodeError, TypeError):
        parsed_value = new_value
    _set_nested(actions[action_name], property_path, parsed_value)
    return patched


def _validate_structure(original: dict, patched: dict) -> None:
    """Ensure no top-level definition keys (triggers, actions, outputs) were lost."""
    lost = set(original.keys()) - set(patched.keys())
    if lost:
        raise ValueError(f"Patch removed definition keys {lost} — aborting PUT")


# ── LLM patch generation ──────────────────────────────────────────────────────

FIX_SYSTEM_PROMPT = """
You are an Azure Logic Apps workflow repair expert.

You will receive:
  - Error details (type, root cause, fix plan, affected action name)
  - The full workflow definition JSON for that action

Generate a list of surgical JSON patches to fix the error.
Each patch specifies:
  - action_name : exact name of the action (from the workflow)
  - property_path : dot-separated path WITHIN the action (e.g. "inputs.retryPolicy")
  - new_value : the new value to set
  - reason : one sentence explaining why this fixes the error

Rules:
  - Only patch what is necessary. Do NOT regenerate the full workflow.
  - Use only action names that exist in the provided workflow.
  - For Timeout errors → add/update inputs.retryPolicy
  - For Authentication errors → update inputs.authentication (type/audience)
  - For Connector Failure → adjust inputs.uri or inputs.body
  - For Payload Issue → fix inputs.body or inputs.queries

Respond only with valid JSON matching the schema.
""".strip()


def _get_llm_fix_instructions(
    llm,
    item: dict,
    definition: dict,
) -> WorkflowFixInstruction:
    """Ask the LLM what specific patches to apply for the failing action only."""
    affected_action = item.get("affected_action", "")
    actions = definition.get("actions", {})
    action_json = json.dumps(
        {affected_action: actions.get(affected_action, {})},
        indent=2,
    )

    user_prompt = (
        f"Run ID        : {item['run_id']}\n"
        f"Error type    : {item['error_type']}\n"
        f"Affected action: {affected_action}\n"
        f"Root cause    : {item['root_cause']}\n"
        f"Fix plan      : {item['fix_plan']}\n\n"
        f"Action definition:\n{action_json}\n\n"
        f"Generate the patches to fix this error."
    )
    return call_llm_structured(llm, FIX_SYSTEM_PROMPT, user_prompt, WorkflowFixInstruction)


# ── Node entrypoint ───────────────────────────────────────────────────────────

def fixer_node(state: dict) -> dict:
    """
    LangGraph node: Fixer
    ----------------------
    1. Read rca_output + workflow_definition from state
    2. For update_workflow items:
         a. Ask LLM for ActionPatch instructions
         b. Apply patches programmatically
         c. Validate structure
         d. PUT to Azure ARM
    3. For retry items: POST to resubmit endpoint
    4. For config_change items: flag for human review
    5. Save fixer_output + patched workflow files to _temp
    """
    logger.info("[Fixer] Starting — applying fixes")

    rca_output: dict = state.get("rca_output", {})
    analysis: list[dict] = rca_output.get("analysis", [])
    workflow_definition: dict = state.get("workflow_definition", {})          # full ARM object
    definition: dict = state.get("workflow_definition_only", {})              # properties.definition
    workflow_name = settings.LOGIC_APP_NAME or state.get("workflow_name", "")

    fix_results = []

    if not analysis:
        logger.warning("[Fixer] No RCA items to process")
        fixer_output = {"fix_results": []}
        save_json(fixer_output, "fixer_output")
        return {**state, "fixer_output": fixer_output}

    token = _get_arm_token()
    llm = get_llm()

    # Save original definition before any modifications for rollback / audit
    save_json(definition, "original_workflow")
    logger.info("[Fixer] Original workflow definition saved to _temp/original_workflow_<timestamp>.json")

    # Work on a single shared copy of the definition block.
    # Multiple patches in one pipeline run accumulate correctly.
    working_definition = copy.deepcopy(definition)
    workflow_was_modified = False

    for item in analysis:
        run_id = item["run_id"]
        action_type = item.get("action_type", "retry")
        confidence = item.get("confidence", 0.0)

        logger.info(
            "[Fixer] run_id=%s action=%s confidence=%.2f",
            run_id, action_type, confidence,
        )

        # ── Safety gate ───────────────────────────────────────────────────────
        if confidence < CONFIDENCE_THRESHOLD:
            fix_results.append({
                "run_id": run_id,
                "status": "skipped",
                "details": (
                    f"Confidence {confidence:.2f} below threshold "
                    f"{CONFIDENCE_THRESHOLD}. Manual review required."
                ),
                "patches_applied": [],
            })
            continue

        try:
            # ── Retry ─────────────────────────────────────────────────────────
            if action_type == "retry":
                _retry_run(token, workflow_name, run_id)
                fix_results.append({
                    "run_id": run_id,
                    "status": "success",
                    "details": "Run resubmitted via ARM resubmit API",
                    "patches_applied": [],
                })

            # ── Update workflow ───────────────────────────────────────────────
            elif action_type == "update_workflow":
                instructions: WorkflowFixInstruction = _get_llm_fix_instructions(
                    llm, item, working_definition  # working_definition is the definition block
                )
                logger.info(
                    "[Fixer] LLM proposed %d patch(es): %s",
                    len(instructions.patches),
                    instructions.summary,
                )

                applied_patches = []
                for patch in instructions.patches:
                    working_definition = _apply_patch(
                        working_definition,
                        patch.action_name,
                        patch.property_path,
                        patch.new_value,
                    )
                    applied_patches.append(patch.model_dump())
                    logger.info(
                        "[Fixer] Patched action='%s' path='%s' reason='%s'",
                        patch.action_name, patch.property_path, patch.reason,
                    )

                workflow_was_modified = True
                fix_results.append({
                    "run_id": run_id,
                    "status": "success",
                    "details": instructions.summary,
                    "patches_applied": applied_patches,
                })

            # ── Config change (human approval required) ───────────────────────
            elif action_type == "config_change":
                fix_results.append({
                    "run_id": run_id,
                    "status": "skipped",
                    "details": (
                        f"Config change requires human action: {item.get('fix_plan', '')}"
                    ),
                    "patches_applied": [],
                })

        except Exception as exc:
            logger.error("[Fixer] Fix failed for run_id=%s: %s", run_id, exc)
            fix_results.append({
                "run_id": run_id,
                "status": "failed",
                "details": str(exc),
                "patches_applied": [],
            })

    # ── Single PUT after all patches are applied ──────────────────────────────
    if workflow_was_modified:
        try:
            _validate_structure(definition, working_definition)

            # Build and save the full PUT body so it can be inspected or
            # re-sent manually via the /update-workflow endpoint.
            put_body = _build_put_body(workflow_definition, working_definition)
            _validate_put_body(put_body)
            save_json(put_body, "fixed_workflow")
            logger.info("[Fixer] Fixed workflow saved to _temp/fixed_workflow_<timestamp>.json")

            logger.info("[Fixer] Pushing patched workflow definition to Azure ARM")
            _put_workflow(token, workflow_name, workflow_definition, working_definition)
            logger.info("[Fixer] Workflow successfully updated in Azure Logic Apps")
        except Exception as exc:
            logger.error("[Fixer] PUT failed: %s", exc)
            # Mark all update_workflow successes as failed
            for r in fix_results:
                if r["status"] == "success" and r["patches_applied"]:
                    r["status"] = "failed"
                    r["details"] = f"Patches generated but PUT failed: {exc}"

    fixer_output = {"fix_results": fix_results}
    path = save_json(fixer_output, "fixer_output")
    logger.info("[Fixer] Saved %d fix results → %s", len(fix_results), path)

    return {**state, "fixer_output": fixer_output}
