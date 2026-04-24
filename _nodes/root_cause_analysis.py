"""
_nodes/root_cause_analysis.py
------------------------------
Root Cause Analysis Node — Step 3 of 4
=======================================
Acts as a planner.  For each classified error the LLM receives:
  - the error details
  - the actual workflow definition (action names, types, inputs)

This lets the LLM identify the *exact* action that failed and propose a
targeted fix referencing real action names — not generic advice.

Input  : state["classifier_output"]  +  state["workflow_definition"]
Output : state["rca_output"]

Saved  : _temp/rca_output_<timestamp>.json

action_type values
------------------
  update_workflow  — workflow JSON needs a patch  (handled by Fixer LLM call)
  retry            — transient error, just resubmit the run
  config_change    — connection / API key change needed (flagged for human)
"""

import json
import logging

from _llm.factory_llm import get_llm, call_llm_structured
from _llm.models_llm import RCAItem, RCAOutput
from _util.file_ops import save_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a senior Azure integration engineer performing root cause analysis
on Azure Logic App failures.

You will receive:
  - Error details (run ID, error type, severity, message, failed action name)
  - The workflow definition JSON (trimmed to action names and types)

Your job:
1. Identify the EXACT action that caused the failure (use affected_action).
2. Explain the root_cause specifically — not generically.
3. Write a concrete fix_plan that an automated system can follow.
4. Choose action_type:
   - update_workflow  → a property in the workflow JSON must change
   - retry            → transient error, re-running will succeed
   - config_change    → an API connection or secret must be updated
5. Provide a confidence score 0.0–1.0.

Respond only with valid JSON matching the schema.
""".strip()


def _build_workflow_summary(workflow_definition: dict) -> str:
    """
    Extract a compact, LLM-friendly summary of workflow actions.
    Avoids sending the full (potentially huge) workflow JSON to the LLM.
    """
    actions = (
        workflow_definition.get("properties", {})
        .get("definition", {})
        .get("actions", {})
    )
    summary = {}
    for name, body in actions.items():
        summary[name] = {
            "type": body.get("type", ""),
            "inputs_keys": list(body.get("inputs", {}).keys()),
            "runAfter": list(body.get("runAfter", {}).keys()),
        }
    return json.dumps(summary, indent=2)


def _analyse_single(llm, classified: dict, workflow_summary: str) -> RCAItem:
    user_prompt = (
        f"Run ID       : {classified['run_id']}\n"
        f"Error type   : {classified['error_type']}\n"
        f"Severity     : {classified['severity']}\n"
        f"Message      : {classified['message']}\n\n"
        f"Workflow actions (name → type, input keys, runAfter):\n"
        f"{workflow_summary}\n\n"
        f"Perform root cause analysis and propose a fix."
    )
    result: RCAOutput = call_llm_structured(
        llm,
        SYSTEM_PROMPT,
        user_prompt,
        RCAOutput,
    )
    item = result.analysis[0]
    item.run_id = classified["run_id"]
    return item


def rca_node(state: dict) -> dict:
    """
    LangGraph node: Root Cause Analysis
    ------------------------------------
    1. Read classifier_output + workflow_definition from state
    2. Build a compact workflow action summary for the LLM
    3. For each classified error, call LLM → RCAItem with affected_action
    4. Assemble RCAOutput, save, return updated state
    """
    logger.info("[RCA] Starting — root cause analysis with workflow context")

    classifier_output: dict = state.get("classifier_output", {})
    classified_errors: list[dict] = classifier_output.get("classified_errors", [])
    workflow_definition: dict = state.get("workflow_definition", {})

    if not classified_errors:
        logger.warning("[RCA] No classified errors to analyse")
        rca_output = {"analysis": []}
        save_json(rca_output, "rca_output")
        return {**state, "rca_output": rca_output}

    workflow_summary = _build_workflow_summary(workflow_definition)
    logger.info("[RCA] Workflow summary built — %d chars", len(workflow_summary))

    llm = get_llm()
    analysis = []

    for classified in classified_errors:
        try:
            item = _analyse_single(llm, classified, workflow_summary)
            analysis.append(item.model_dump())
            logger.info(
                "[RCA] run_id=%s affected_action=%s action=%s confidence=%.2f",
                item.run_id, item.affected_action, item.action_type, item.confidence,
            )
        except Exception as exc:
            logger.error("[RCA] Failed for run_id=%s: %s", classified.get("run_id"), exc)
            analysis.append({
                "run_id": classified.get("run_id", "unknown"),
                "error_type": classified.get("error_type", "Unknown"),
                "affected_action": "unknown",
                "root_cause": "RCA failed — manual investigation required",
                "fix_plan": "Review run logs manually in Azure portal",
                "action_type": "retry",
                "confidence": 0.0,
            })

    rca_output = {"analysis": analysis}
    path = save_json(rca_output, "rca_output")
    logger.info("[RCA] Saved %d RCA results → %s", len(analysis), path)

    return {**state, "rca_output": rca_output}
