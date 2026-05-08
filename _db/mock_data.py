"""
Mock data for development/demo when SAP HANA is not available.
"""
from datetime import datetime, timedelta
import random

MOCK_INCIDENTS = [
    {"ID": "INC-001", "SUBSCRIPTION_ID": "sub-azure-001", "INTEGRATION_SCENARIO": "SalesOrder_to_ERP", "ERROR_TYPE": "Connectivity Error", "STATUS": "In Progress", "MESSAGE": "Connection timeout to ERP system", "ROOT_CAUSE": "Network firewall rule blocking port 443", "AUTO_FIX_APPLIED": False, "RESOLUTION_TIME": 320, "CREATED_AT": datetime.now() - timedelta(hours=2), "UPDATED_AT": datetime.now() - timedelta(hours=1)},
    {"ID": "INC-002", "SUBSCRIPTION_ID": "sub-azure-002", "INTEGRATION_SCENARIO": "Invoice_Sync", "ERROR_TYPE": "Credential Error", "STATUS": "Auto Fixed", "MESSAGE": "OAuth token expired", "ROOT_CAUSE": "Token refresh interval misconfigured", "AUTO_FIX_APPLIED": True, "RESOLUTION_TIME": 45, "CREATED_AT": datetime.now() - timedelta(hours=5), "UPDATED_AT": datetime.now() - timedelta(hours=4)},
    {"ID": "INC-003", "SUBSCRIPTION_ID": "sub-azure-003", "INTEGRATION_SCENARIO": "Customer_Master_Replication", "ERROR_TYPE": "Artifact Missing", "STATUS": "Ticket Created", "MESSAGE": "Referenced iFlow artifact not found", "ROOT_CAUSE": "Deployment package corrupted during last release", "AUTO_FIX_APPLIED": False, "RESOLUTION_TIME": None, "CREATED_AT": datetime.now() - timedelta(hours=3), "UPDATED_AT": datetime.now() - timedelta(minutes=30)},
    {"ID": "INC-004", "SUBSCRIPTION_ID": "sub-azure-004", "INTEGRATION_SCENARIO": "HR_Data_Sync", "ERROR_TYPE": "Timeout Error", "STATUS": "Fix Failed", "MESSAGE": "Request timed out after 30s", "ROOT_CAUSE": "Target system under heavy load", "AUTO_FIX_APPLIED": False, "RESOLUTION_TIME": None, "CREATED_AT": datetime.now() - timedelta(hours=1), "UPDATED_AT": datetime.now() - timedelta(minutes=15)},
    {"ID": "INC-005", "SUBSCRIPTION_ID": "sub-azure-005", "INTEGRATION_SCENARIO": "Payment_Gateway_Integration", "ERROR_TYPE": "SMTP Error", "STATUS": "RCA Complete", "MESSAGE": "Email notification failed to send", "ROOT_CAUSE": "SMTP relay misconfiguration", "AUTO_FIX_APPLIED": False, "RESOLUTION_TIME": 180, "CREATED_AT": datetime.now() - timedelta(hours=4), "UPDATED_AT": datetime.now() - timedelta(hours=2)},
    {"ID": "INC-006", "SUBSCRIPTION_ID": "sub-azure-006", "INTEGRATION_SCENARIO": "Inventory_Update", "ERROR_TYPE": "Connectivity Error", "STATUS": "In Progress", "MESSAGE": "SSL handshake failure", "ROOT_CAUSE": "Certificate expired on target endpoint", "AUTO_FIX_APPLIED": False, "RESOLUTION_TIME": None, "CREATED_AT": datetime.now() - timedelta(minutes=45), "UPDATED_AT": datetime.now() - timedelta(minutes=10)},
    {"ID": "INC-007", "SUBSCRIPTION_ID": "sub-azure-007", "INTEGRATION_SCENARIO": "SalesOrder_to_ERP", "ERROR_TYPE": "Unknown Error", "STATUS": "In Progress", "MESSAGE": "Unexpected null pointer exception", "ROOT_CAUSE": "Missing input mapping for optional field", "AUTO_FIX_APPLIED": False, "RESOLUTION_TIME": None, "CREATED_AT": datetime.now() - timedelta(hours=6), "UPDATED_AT": datetime.now() - timedelta(hours=5)},
    {"ID": "INC-008", "SUBSCRIPTION_ID": "sub-azure-008", "INTEGRATION_SCENARIO": "Finance_Reporting", "ERROR_TYPE": "Credential Error", "STATUS": "Auto Fixed", "MESSAGE": "API key rotation failed", "ROOT_CAUSE": "Vault access policy outdated", "AUTO_FIX_APPLIED": True, "RESOLUTION_TIME": 60, "CREATED_AT": datetime.now() - timedelta(hours=8), "UPDATED_AT": datetime.now() - timedelta(hours=7)},
    {"ID": "INC-009", "SUBSCRIPTION_ID": "sub-azure-009", "INTEGRATION_SCENARIO": "Logistics_Tracking", "ERROR_TYPE": "Connectivity Error", "STATUS": "In Progress", "MESSAGE": "Remote host unreachable", "ROOT_CAUSE": "DNS resolution failure for endpoint", "AUTO_FIX_APPLIED": False, "RESOLUTION_TIME": None, "CREATED_AT": datetime.now() - timedelta(hours=3), "UPDATED_AT": datetime.now() - timedelta(hours=2)},
    {"ID": "INC-010", "SUBSCRIPTION_ID": "sub-azure-010", "INTEGRATION_SCENARIO": "Purchase_Order_Sync", "ERROR_TYPE": "Timeout Error", "STATUS": "Fix Applied Pending", "MESSAGE": "Batch processing timeout exceeded", "ROOT_CAUSE": "Large payload size causing memory pressure", "AUTO_FIX_APPLIED": True, "RESOLUTION_TIME": 420, "CREATED_AT": datetime.now() - timedelta(hours=10), "UPDATED_AT": datetime.now() - timedelta(hours=9)},
    {"ID": "INC-011", "SUBSCRIPTION_ID": "sub-azure-011", "INTEGRATION_SCENARIO": "Vendor_Master_Sync", "ERROR_TYPE": "Artifact Missing", "STATUS": "In Progress", "MESSAGE": "Mapping artifact version mismatch", "ROOT_CAUSE": "Deployed version does not match configured version", "AUTO_FIX_APPLIED": False, "RESOLUTION_TIME": None, "CREATED_AT": datetime.now() - timedelta(minutes=90), "UPDATED_AT": datetime.now() - timedelta(minutes=30)},
    {"ID": "INC-012", "SUBSCRIPTION_ID": "sub-azure-012", "INTEGRATION_SCENARIO": "Customer_360_Integration", "ERROR_TYPE": "Unknown Error", "STATUS": "In Progress", "MESSAGE": "Deserialization error in XML processing", "ROOT_CAUSE": "Schema version incompatibility", "AUTO_FIX_APPLIED": False, "RESOLUTION_TIME": None, "CREATED_AT": datetime.now() - timedelta(hours=2), "UPDATED_AT": datetime.now() - timedelta(hours=1)},
    {"ID": "INC-013", "SUBSCRIPTION_ID": "sub-azure-013", "INTEGRATION_SCENARIO": "Invoice_Sync", "ERROR_TYPE": "SMTP Error", "STATUS": "In Progress", "MESSAGE": "TLS negotiation failed with mail server", "ROOT_CAUSE": "TLS version mismatch", "AUTO_FIX_APPLIED": False, "RESOLUTION_TIME": None, "CREATED_AT": datetime.now() - timedelta(hours=1), "UPDATED_AT": datetime.now() - timedelta(minutes=20)},
    {"ID": "INC-014", "SUBSCRIPTION_ID": "sub-azure-014", "INTEGRATION_SCENARIO": "HR_Data_Sync", "ERROR_TYPE": "Credential Error", "STATUS": "Auto Fixed", "MESSAGE": "LDAP bind failure", "ROOT_CAUSE": "Service account password expired", "AUTO_FIX_APPLIED": True, "RESOLUTION_TIME": 30, "CREATED_AT": datetime.now() - timedelta(hours=12), "UPDATED_AT": datetime.now() - timedelta(hours=11)},
    {"ID": "INC-015", "SUBSCRIPTION_ID": "sub-azure-015", "INTEGRATION_SCENARIO": "SalesOrder_to_ERP", "ERROR_TYPE": "Fix Failed", "STATUS": "Fix Failed", "MESSAGE": "Auto-remediation script failed", "ROOT_CAUSE": "Rollback not supported for this artifact type", "AUTO_FIX_APPLIED": False, "RESOLUTION_TIME": None, "CREATED_AT": datetime.now() - timedelta(hours=7), "UPDATED_AT": datetime.now() - timedelta(hours=6)},
    {"ID": "INC-016", "SUBSCRIPTION_ID": "sub-azure-016", "INTEGRATION_SCENARIO": "Inventory_Update", "ERROR_TYPE": "Connectivity Error", "STATUS": "In Progress", "MESSAGE": "Connection pool exhausted", "ROOT_CAUSE": "Thread leak in connection handler", "AUTO_FIX_APPLIED": False, "RESOLUTION_TIME": None, "CREATED_AT": datetime.now() - timedelta(minutes=120), "UPDATED_AT": datetime.now() - timedelta(minutes=60)},
    {"ID": "INC-017", "SUBSCRIPTION_ID": "sub-azure-017", "INTEGRATION_SCENARIO": "Payment_Gateway_Integration", "ERROR_TYPE": "Timeout Error", "STATUS": "In Progress", "MESSAGE": "Gateway response delayed", "ROOT_CAUSE": "Payment provider SLA breach", "AUTO_FIX_APPLIED": False, "RESOLUTION_TIME": None, "CREATED_AT": datetime.now() - timedelta(minutes=30), "UPDATED_AT": datetime.now() - timedelta(minutes=5)},
]

MOCK_FAILED_MESSAGES = [
    {"ID": "MSG-001", "SUBSCRIPTION_ID": "sub-azure-001", "IFLOW_NAME": "SalesOrder_to_ERP", "STATUS": "Failed", "ERROR_TYPE": "Connectivity Error", "CREATED_AT": datetime.now() - timedelta(hours=2)},
    {"ID": "MSG-002", "SUBSCRIPTION_ID": "sub-azure-002", "IFLOW_NAME": "Invoice_Sync", "STATUS": "Retry", "ERROR_TYPE": "Timeout Error", "CREATED_AT": datetime.now() - timedelta(hours=3)},
    {"ID": "MSG-003", "SUBSCRIPTION_ID": "sub-azure-003", "IFLOW_NAME": "Customer_Master_Replication", "STATUS": "Failed", "ERROR_TYPE": "Artifact Missing", "CREATED_AT": datetime.now() - timedelta(hours=1)},
    {"ID": "MSG-004", "SUBSCRIPTION_ID": "sub-azure-004", "IFLOW_NAME": "HR_Data_Sync", "STATUS": "Processing", "ERROR_TYPE": "Credential Error", "CREATED_AT": datetime.now() - timedelta(minutes=45)},
    {"ID": "MSG-005", "SUBSCRIPTION_ID": "sub-azure-005", "IFLOW_NAME": "Payment_Gateway_Integration", "STATUS": "Failed", "ERROR_TYPE": "SMTP Error", "CREATED_AT": datetime.now() - timedelta(hours=4)},
    {"ID": "MSG-006", "SUBSCRIPTION_ID": "sub-azure-006", "IFLOW_NAME": "Inventory_Update", "STATUS": "Failed", "ERROR_TYPE": "Connectivity Error", "CREATED_AT": datetime.now() - timedelta(minutes=30)},
    {"ID": "MSG-007", "SUBSCRIPTION_ID": "sub-azure-007", "IFLOW_NAME": "Finance_Reporting", "STATUS": "Retry", "ERROR_TYPE": "Unknown Error", "CREATED_AT": datetime.now() - timedelta(hours=5)},
    {"ID": "MSG-008", "SUBSCRIPTION_ID": "sub-azure-008", "IFLOW_NAME": "Logistics_Tracking", "STATUS": "Failed", "ERROR_TYPE": "Connectivity Error", "CREATED_AT": datetime.now() - timedelta(hours=2)},
    {"ID": "MSG-009", "SUBSCRIPTION_ID": "sub-azure-009", "IFLOW_NAME": "Purchase_Order_Sync", "STATUS": "Processing", "ERROR_TYPE": "Timeout Error", "CREATED_AT": datetime.now() - timedelta(minutes=15)},
    {"ID": "MSG-010", "SUBSCRIPTION_ID": "sub-azure-010", "IFLOW_NAME": "Vendor_Master_Sync", "STATUS": "Failed", "ERROR_TYPE": "Artifact Missing", "CREATED_AT": datetime.now() - timedelta(hours=1)},
]


def get_mock_kpis() -> dict:
    total = len(MOCK_INCIDENTS)
    in_progress = sum(1 for i in MOCK_INCIDENTS if i["STATUS"] == "In Progress")
    fix_failed = sum(1 for i in MOCK_INCIDENTS if i["STATUS"] == "Fix Failed")
    auto_fixed = sum(1 for i in MOCK_INCIDENTS if i["STATUS"] == "Auto Fixed")
    failed_msgs = len(MOCK_FAILED_MESSAGES)
    auto_fix_rate = round((auto_fixed / total * 100), 1) if total > 0 else 0
    resolved = [i["RESOLUTION_TIME"] for i in MOCK_INCIDENTS if i["RESOLUTION_TIME"] is not None]
    avg_resolution = round(sum(resolved) / len(resolved), 1) if resolved else 0
    rca_done = sum(1 for i in MOCK_INCIDENTS if i["ROOT_CAUSE"])
    rca_coverage = round((rca_done / total * 100), 1) if total > 0 else 0
    return {
        "inProgress": in_progress,
        "totalIncidents": total,
        "pendingApproval": 0,
        "fixFailed": fix_failed,
        "autoFixed": auto_fixed,
        "failedMessages": failed_msgs,
        "autoFixRate": auto_fix_rate,
        "avgResolutionTime": avg_resolution,
        "rcaCoverage": rca_coverage,
    }


def get_mock_status_breakdown() -> list:
    from collections import Counter
    counts = Counter(i["STATUS"] for i in MOCK_INCIDENTS)
    return [{"status": k, "count": v} for k, v in counts.items()]


def get_mock_error_distribution() -> list:
    from collections import Counter
    counts = Counter(i["ERROR_TYPE"] for i in MOCK_INCIDENTS)
    return [{"errorType": k, "count": v} for k, v in counts.items()]


def get_mock_top_failing_artifacts(limit: int = 10) -> list:
    from collections import Counter
    counts = Counter(i["INTEGRATION_SCENARIO"] for i in MOCK_INCIDENTS)
    return [{"artifact": k, "failureCount": v} for k, v in counts.most_common(limit)]


def get_mock_failure_over_time(hours: int = 24) -> list:
    from collections import defaultdict
    buckets = defaultdict(int)
    cutoff = datetime.now() - timedelta(hours=hours)
    for inc in MOCK_INCIDENTS:
        ts = inc["CREATED_AT"]
        if ts >= cutoff:
            bucket_key = ts.strftime("%Y-%m-%dT%H:00:00")
            buckets[bucket_key] += 1
    return sorted([{"timestamp": k, "count": v} for k, v in buckets.items()], key=lambda x: x["timestamp"])


def paginate(items: list, page: int, page_size: int, search: str = "", search_fields: list = None) -> dict:
    if search and search_fields:
        items = [i for i in items if any(search.lower() in str(i.get(f, "")).lower() for f in search_fields)]
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": (total + page_size - 1) // page_size,
    }
