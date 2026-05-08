"""
Dashboard service — tries HANA first, falls back to mock data.
"""
import logging
from datetime import datetime

from _db.hana_client import hana
from _db.mock_data import (
    get_mock_kpis, get_mock_status_breakdown, get_mock_error_distribution,
    get_mock_top_failing_artifacts, get_mock_failure_over_time, paginate,
    MOCK_INCIDENTS, MOCK_FAILED_MESSAGES,
)
from _dashboard import dashboard_queries as Q

logger = logging.getLogger(__name__)


def _use_hana() -> bool:
    return hana.get_connection() is not None


def _fmt_incident(row: dict) -> dict:
    return {
        "id": row.get("ID", ""),
        "subscriptionId": row.get("SUBSCRIPTION_ID", ""),
        "integrationScenario": row.get("INTEGRATION_SCENARIO", ""),
        "errorType": row.get("ERROR_TYPE", ""),
        "status": row.get("STATUS", ""),
        "message": row.get("MESSAGE"),
        "rootCause": row.get("ROOT_CAUSE"),
        "autoFixApplied": bool(row.get("AUTO_FIX_APPLIED", False)),
        "resolutionTime": row.get("RESOLUTION_TIME"),
        "createdAt": str(row.get("CREATED_AT", "")),
        "updatedAt": str(row.get("UPDATED_AT", "")),
    }


def _fmt_message(row: dict) -> dict:
    return {
        "id": row.get("ID", ""),
        "subscriptionId": row.get("SUBSCRIPTION_ID", ""),
        "iflowName": row.get("IFLOW_NAME", ""),
        "status": row.get("STATUS", ""),
        "errorType": row.get("ERROR_TYPE", ""),
        "createdAt": str(row.get("CREATED_AT", "")),
    }


def get_kpis() -> dict:
    if _use_hana():
        rows = hana.execute_query(Q.KPI_QUERY)
        fmsg_count = hana.execute_scalar(Q.FAILED_MESSAGES_COUNT_QUERY, default=0)
        if rows:
            r = rows[0]
            return {
                "inProgress": int(r.get("IN_PROGRESS", 0) or 0),
                "totalIncidents": int(r.get("TOTAL_INCIDENTS", 0) or 0),
                "pendingApproval": int(r.get("PENDING_APPROVAL", 0) or 0),
                "fixFailed": int(r.get("FIX_FAILED", 0) or 0),
                "autoFixed": int(r.get("AUTO_FIXED", 0) or 0),
                "failedMessages": int(fmsg_count or 0),
                "autoFixRate": float(r.get("AUTO_FIX_RATE", 0) or 0),
                "avgResolutionTime": float(r.get("AVG_RESOLUTION_TIME", 0) or 0),
                "rcaCoverage": float(r.get("RCA_COVERAGE", 0) or 0),
            }
    return get_mock_kpis()


def get_status_breakdown() -> list:
    if _use_hana():
        rows = hana.execute_query(Q.STATUS_BREAKDOWN_QUERY)
        if rows:
            return [{"status": r["STATUS"], "count": int(r["COUNT"])} for r in rows]
    return get_mock_status_breakdown()


def get_error_distribution() -> list:
    if _use_hana():
        rows = hana.execute_query(Q.ERROR_DISTRIBUTION_QUERY)
        if rows:
            return [{"errorType": r["ERROR_TYPE"], "count": int(r["COUNT"])} for r in rows]
    return get_mock_error_distribution()


def get_top_failing_artifacts(limit: int = 10) -> list:
    if _use_hana():
        rows = hana.execute_query(Q.TOP_FAILING_ARTIFACTS_QUERY, (limit,))
        if rows:
            return [{"artifact": r["ARTIFACT"], "failureCount": int(r["FAILURE_COUNT"])} for r in rows]
    return get_mock_top_failing_artifacts(limit)


def get_failure_over_time(hours: int = 24) -> list:
    if _use_hana():
        rows = hana.execute_query(Q.FAILURE_OVER_TIME_QUERY, (-hours * 3600,))
        if rows:
            return [{"timestamp": r["TIMESTAMP"], "count": int(r["COUNT"])} for r in rows]
    return get_mock_failure_over_time(hours)


def get_incidents(page: int = 1, page_size: int = 10, search: str = "") -> dict:
    if _use_hana():
        offset = (page - 1) * page_size
        rows = hana.execute_query(Q.INCIDENTS_LIST_QUERY, (page_size, offset))
        items = [_fmt_incident(r) for r in rows]
        return {"items": items, "total": len(items), "page": page, "pageSize": page_size, "totalPages": 1}
    raw = [_fmt_incident(i) for i in MOCK_INCIDENTS]
    return paginate(raw, page, page_size, search, ["integrationScenario", "errorType", "status", "subscriptionId"])


def get_failed_messages(page: int = 1, page_size: int = 10, search: str = "") -> dict:
    if _use_hana():
        offset = (page - 1) * page_size
        rows = hana.execute_query(Q.FAILED_MESSAGES_LIST_QUERY, (page_size, offset))
        items = [_fmt_message(r) for r in rows]
        return {"items": items, "total": len(items), "page": page, "pageSize": page_size, "totalPages": 1}
    raw = [_fmt_message(m) for m in MOCK_FAILED_MESSAGES]
    return paginate(raw, page, page_size, search, ["iflowName", "status", "errorType", "subscriptionId"])
