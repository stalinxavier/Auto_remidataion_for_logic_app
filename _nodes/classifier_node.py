"""
_nodes/classifier_node.py
-------------------------
Classifier Node — Step 2 of 4
==============================
Sends each raw error to the LLM and receives a structured classification.

Input  : state["observer_output"]
Output : state["classifier_output"]

Saved  : _temp/classifier_output_<timestamp>.json

Error categories
----------------
  Authentication | Timeout | Connector Failure | Payload Issue | Unknown
"""

import logging

from _llm.factory_llm import get_llm, call_llm_structured
from _llm.models_llm import ClassifiedError, ClassifierOutput
from _util.file_ops import save_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are an Azure Logic Apps error classification expert.
Classify each error into exactly one of:
  - Authentication
  - Timeout
  - Connector Failure
  - Payload Issue
  - Unknown

Assign severity as one of: Low | Medium | High | Critical.
Write a concise one-sentence message explaining the error.
Respond only with the JSON specified by the schema.
""".strip()


def _classify_single(llm, error: dict) -> ClassifiedError:
    user_prompt = (
        f"Run ID  : {error['run_id']}\n"
        f"Message : {error['error_message']}\n"
        f"Code    : {error.get('error_code', '')}\n"
        f"Classify this error."
    )
    result: ClassifierOutput = call_llm_structured(
        llm,
        SYSTEM_PROMPT,
        user_prompt,
        ClassifierOutput,
    )
    # LLM returns a list; take the first item
    item = result.classified_errors[0]
    item.run_id = error["run_id"]
    return item


def classifier_node(state: dict) -> dict:
    """
    LangGraph node: Classifier
    --------------------------
    1. Read observer_output from state
    2. For each error, call LLM → ClassifiedError
    3. Assemble ClassifierOutput, save, return updated state
    """
    logger.info("[Classifier] Starting — classifying errors with LLM")

    observer_output: dict = state.get("observer_output", {})
    errors: list[dict] = observer_output.get("errors", [])

    if not errors:
        logger.warning("[Classifier] No errors to classify")
        classifier_output = {"classified_errors": []}
        save_json(classifier_output, "classifier_output")
        return {**state, "classifier_output": classifier_output}

    llm = get_llm()
    classified = []

    for error in errors:
        try:
            item = _classify_single(llm, error)
            classified.append(item.model_dump())
            logger.info("[Classifier] run_id=%s → %s (%s)", item.run_id, item.error_type, item.severity)
        except Exception as exc:
            logger.error("[Classifier] Failed for run_id=%s: %s", error.get("run_id"), exc)
            classified.append({
                "run_id": error.get("run_id", "unknown"),
                "error_type": "Unknown",
                "severity": "High",
                "message": str(exc),
            })

    classifier_output = {"classified_errors": classified}
    path = save_json(classifier_output, "classifier_output")
    logger.info("[Classifier] Saved %d classifications → %s", len(classified), path)

    return {**state, "classifier_output": classifier_output}
