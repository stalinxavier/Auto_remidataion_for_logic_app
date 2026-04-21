"""
_nodes/root_cause_analysis.py
------------------------------
Root Cause Analysis Node — Step 3 of 4
=======================================
Acts as a planner: for each classified error it identifies WHY the error
occurred and recommends an automated fix action.

Input  : state["classifier_output"]
Output : state["rca_output"]

Saved  : _temp/rca_output_<timestamp>.json

action_type values
------------------
  update_workflow | retry | config_change
"""

import logging

from _llm.factory_llm import get_llm, call_llm_structured
from _llm.models_llm import RCAItem, RCAOutput
from _util.file_ops import save_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a senior Azure integration engineer performing root cause analysis
on Logic App failures.

For each error:
1. Identify the root cause (be specific, not generic).
2. Write a concrete, step-by-step fix_plan that can be automated.
3. Choose action_type:
   - update_workflow  → the workflow JSON definition needs a patch
   - retry            → the run should simply be retried (transient error)
   - config_change    → a connection, parameter, or setting must be changed
4. Provide a confidence score between 0.0 and 1.0.

Respond only with the JSON specified by the schema.
""".strip()


def _analyse_single(llm, classified: dict) -> RCAItem:
    user_prompt = (
        f"Run ID     : {classified['run_id']}\n"
        f"Error type : {classified['error_type']}\n"
        f"Severity   : {classified['severity']}\n"
        f"Message    : {classified['message']}\n"
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
    1. Read classifier_output from state
    2. For each classified error, call LLM → RCAItem
    3. Assemble RCAOutput, save, return updated state
    """
    logger.info("[RCA] Starting — root cause analysis with LLM")

    classifier_output: dict = state.get("classifier_output", {})
    classified_errors: list[dict] = classifier_output.get("classified_errors", [])

    if not classified_errors:
        logger.warning("[RCA] No classified errors to analyse")
        rca_output = {"analysis": []}
        save_json(rca_output, "rca_output")
        return {**state, "rca_output": rca_output}

    llm = get_llm()
    analysis = []

    for classified in classified_errors:
        try:
            item = _analyse_single(llm, classified)
            analysis.append(item.model_dump())
            logger.info(
                "[RCA] run_id=%s action=%s confidence=%.2f",
                item.run_id, item.action_type, item.confidence,
            )
        except Exception as exc:
            logger.error("[RCA] Failed for run_id=%s: %s", classified.get("run_id"), exc)
            analysis.append({
                "run_id": classified.get("run_id", "unknown"),
                "error_type": classified.get("error_type", "Unknown"),
                "root_cause": "RCA failed — manual investigation required",
                "fix_plan": "Review run logs manually",
                "action_type": "retry",
                "confidence": 0.0,
            })

    rca_output = {"analysis": analysis}
    path = save_json(rca_output, "rca_output")
    logger.info("[RCA] Saved %d RCA results → %s", len(analysis), path)

    return {**state, "rca_output": rca_output}
