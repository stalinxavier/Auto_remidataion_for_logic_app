"""
Collects and stores metrics from the remediation pipeline into HANA.
Called after each pipeline run to persist results.
"""
import logging
import uuid
from datetime import datetime
from _db.hana_client import hana

logger = logging.getLogger(__name__)


def store_incident(incident_data: dict) -> bool:
    """Persist a pipeline result as an incident record in HANA."""
    conn = hana.get_connection()
    if conn is None:
        logger.info("HANA not available — skipping incident persistence")
        return False
    try:
        sql = """
        UPSERT CPI_MONITORING.INCIDENTS
        (ID, SUBSCRIPTION_ID, INTEGRATION_SCENARIO, ERROR_TYPE, STATUS,
         MESSAGE, ROOT_CAUSE, AUTO_FIX_APPLIED, RESOLUTION_TIME, CREATED_AT, UPDATED_AT)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        WITH PRIMARY KEY
        """
        cursor = conn.cursor()
        cursor.execute(sql, (
            incident_data.get("id", str(uuid.uuid4())),
            incident_data.get("subscription_id", ""),
            incident_data.get("integration_scenario", ""),
            incident_data.get("error_type", "Unknown"),
            incident_data.get("status", "In Progress"),
            incident_data.get("message", ""),
            incident_data.get("root_cause", ""),
            incident_data.get("auto_fix_applied", False),
            incident_data.get("resolution_time"),
            datetime.now(),
            datetime.now(),
        ))
        conn.commit()
        return True
    except Exception as exc:
        logger.error("Failed to store incident: %s", exc)
        return False


def store_failed_message(msg_data: dict) -> bool:
    """Persist a failed message record in HANA."""
    conn = hana.get_connection()
    if conn is None:
        return False
    try:
        sql = """
        INSERT INTO CPI_MONITORING.FAILED_MESSAGES
        (ID, SUBSCRIPTION_ID, IFLOW_NAME, STATUS, ERROR_TYPE, PAYLOAD, CREATED_AT)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor = conn.cursor()
        cursor.execute(sql, (
            msg_data.get("id", str(uuid.uuid4())),
            msg_data.get("subscription_id", ""),
            msg_data.get("iflow_name", ""),
            msg_data.get("status", "Failed"),
            msg_data.get("error_type", "Unknown"),
            msg_data.get("payload", ""),
            datetime.now(),
        ))
        conn.commit()
        return True
    except Exception as exc:
        logger.error("Failed to store failed message: %s", exc)
        return False
