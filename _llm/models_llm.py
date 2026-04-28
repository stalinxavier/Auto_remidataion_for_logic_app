"""
_llm/models_llm.py
------------------
Pydantic schemas for all structured LLM outputs.
Every LLM call must return one of these models — no plain text.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional, Union


# ── Classifier ────────────────────────────────────────────────────────────────

class ClassifiedError(BaseModel):
    run_id: str = Field(..., description="Logic App run ID")
    error_type: Literal[
        "Authentication",
        "Timeout",
        "Connector Failure",
        "Payload Issue",
        "Unknown",
    ] = Field(..., description="Error category")
    severity: Literal["Low", "Medium", "High", "Critical"] = Field(
        ..., description="Impact severity"
    )
    message: str = Field(..., description="Short human-readable summary")


class ClassifierOutput(BaseModel):
    classified_errors: List[ClassifiedError]


# ── Root Cause Analysis ────────────────────────────────────────────────────────

class RCAItem(BaseModel):
    run_id: str
    error_type: str
    affected_action: str = Field(
        ...,
        description="Exact action name from the workflow definition that caused the failure",
    )
    root_cause: str = Field(..., description="Why the error occurred")
    fix_plan: str = Field(..., description="Step-by-step remediation plan")
    action_type: Literal["update_workflow", "retry", "config_change"] = Field(
        ..., description="Kind of automated action to take"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="LLM confidence score 0–1"
    )


class RCAOutput(BaseModel):
    analysis: List[RCAItem]


# ── Fixer — surgical patch instructions ──────────────────────────────────────

class ActionPatch(BaseModel):
    """
    A single targeted change to one property inside a workflow action.

    property_path uses dot notation relative to the action root.
    Examples:
      "inputs.retryPolicy"
      "inputs.uri"
      "runAfter"
    """
    action_name: str = Field(..., description="Exact name of the action to patch")
    property_path: str = Field(..., description="Dot-separated path within the action")
    new_value: str = Field(
        ...,
        description=(
            "New value to set at property_path, serialized as a JSON string. "
            "Scalars: '\"mystring\"', '42', 'true', 'null'. "
            "Objects/arrays: '{\"count\": 3}', '[\"a\",\"b\"]'."
        ),
    )
    reason: str = Field(..., description="One-line explanation of why this change fixes the error")


class WorkflowFixInstruction(BaseModel):
    """
    Complete set of patches the LLM wants applied to the workflow.
    The Fixer applies each ActionPatch programmatically — never rewrites the whole JSON.
    """
    patches: List[ActionPatch]
    summary: str = Field(..., description="Human-readable description of what was changed")


# ── Fixer result ──────────────────────────────────────────────────────────────

class FixResult(BaseModel):
    run_id: str
    status: Literal["success", "failed", "skipped"]
    details: str
    patches_applied: List[dict] = Field(
        default_factory=list,
        description="List of ActionPatch dicts that were applied",
    )
