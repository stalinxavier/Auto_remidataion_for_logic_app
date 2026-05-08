from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class KPIResponse(BaseModel):
    inProgress: int
    totalIncidents: int
    pendingApproval: int
    fixFailed: int
    autoFixed: int
    failedMessages: int
    autoFixRate: float
    avgResolutionTime: float
    rcaCoverage: float


class StatusBreakdownItem(BaseModel):
    status: str
    count: int


class ErrorDistributionItem(BaseModel):
    errorType: str
    count: int


class TopArtifactItem(BaseModel):
    artifact: str
    failureCount: int


class FailureTimeItem(BaseModel):
    timestamp: str
    count: int


class IncidentItem(BaseModel):
    id: str
    subscriptionId: str
    integrationScenario: str
    errorType: str
    status: str
    message: Optional[str] = None
    rootCause: Optional[str] = None
    autoFixApplied: bool = False
    resolutionTime: Optional[int] = None
    createdAt: str
    updatedAt: str


class FailedMessageItem(BaseModel):
    id: str
    subscriptionId: str
    iflowName: str
    status: str
    errorType: str
    createdAt: str


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    pageSize: int
    totalPages: int


class APIResponse(BaseModel):
    success: bool
    data: object
    message: str = "Fetched successfully"
