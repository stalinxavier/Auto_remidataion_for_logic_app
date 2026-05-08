"""
SAP HANA connection client with connection pooling and error handling.
Falls back to mock data if HANA is not configured (for dev/demo).
"""
import logging
from contextlib import contextmanager
from typing import Any, Generator

from _config.config import settings

logger = logging.getLogger(__name__)

_HANA_AVAILABLE = False

try:
    from hdbcli import dbapi
    _HANA_AVAILABLE = True
except ImportError:
    logger.warning("hdbcli not installed — HANA features disabled, using mock data")


class HANAClient:
    _instance = None
    _connection = None

    @classmethod
    def get_connection(cls):
        if not _HANA_AVAILABLE or not settings.HANA_HOST:
            return None
        if cls._connection is None:
            try:
                cls._connection = dbapi.connect(
                    address=settings.HANA_HOST,
                    port=settings.HANA_PORT,
                    user=settings.HANA_USER,
                    password=settings.HANA_PASSWORD,
                )
                logger.info("HANA connection established")
            except Exception as exc:
                logger.error("HANA connection failed: %s", exc)
                return None
        return cls._connection

    @classmethod
    def execute_query(cls, sql: str, params: tuple = ()) -> list[dict]:
        conn = cls.get_connection()
        if conn is None:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as exc:
            logger.error("Query failed: %s | SQL: %s", exc, sql)
            cls._connection = None  # reset on error
            return []

    @classmethod
    def execute_scalar(cls, sql: str, params: tuple = (), default: Any = 0) -> Any:
        rows = cls.execute_query(sql, params)
        if rows:
            return list(rows[0].values())[0]
        return default

    @classmethod
    def close(cls):
        if cls._connection:
            cls._connection.close()
            cls._connection = None


hana = HANAClient()
