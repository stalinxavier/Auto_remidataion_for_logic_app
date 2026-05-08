"""
FastAPI router for all dashboard API endpoints.
"""
from fastapi import APIRouter, Query
from _dashboard.dashboard_models import APIResponse
from _dashboard import dashboard_service as svc

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/kpis")
def get_kpis():
    data = svc.get_kpis()
    return APIResponse(success=True, data=data, message="KPIs fetched successfully")


@router.get("/dashboard/status-breakdown")
def get_status_breakdown():
    data = svc.get_status_breakdown()
    return APIResponse(success=True, data=data, message="Status breakdown fetched")


@router.get("/dashboard/error-distribution")
def get_error_distribution():
    data = svc.get_error_distribution()
    return APIResponse(success=True, data=data, message="Error distribution fetched")


@router.get("/dashboard/top-failing-artifacts")
def get_top_failing_artifacts(limit: int = Query(default=10, ge=1, le=50)):
    data = svc.get_top_failing_artifacts(limit)
    return APIResponse(success=True, data=data, message="Top failing artifacts fetched")


@router.get("/dashboard/failure-over-time")
def get_failure_over_time(hours: int = Query(default=24, ge=1, le=168)):
    data = svc.get_failure_over_time(hours)
    return APIResponse(success=True, data=data, message="Failure over time fetched")


@router.get("/incidents")
def list_incidents(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
    search: str = Query(default=""),
):
    data = svc.get_incidents(page, pageSize, search)
    return APIResponse(success=True, data=data, message="Incidents fetched")


@router.get("/failed-messages")
def list_failed_messages(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
    search: str = Query(default=""),
):
    data = svc.get_failed_messages(page, pageSize, search)
    return APIResponse(success=True, data=data, message="Failed messages fetched")
