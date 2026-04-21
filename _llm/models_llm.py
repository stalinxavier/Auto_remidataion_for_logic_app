"""
_llm/models_llm.py
------------------
Pydantic schemas for all structured LLM outputs.
Every LLM call must return one of these models — no plain text.
"""

from pydantic import BaseModel, Field
from typing import List, Literal


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


# ── Fixer ─────────────────────────────────────────────────────────────────────

class FixResult(BaseModel):
    run_id: str
    status: Literal["success", "failed", "skipped"]
    details: str
    workflow_patch: dict = Field(
        default_factory=dict,
        description="JSON patch applied to the workflow definition",
    )
