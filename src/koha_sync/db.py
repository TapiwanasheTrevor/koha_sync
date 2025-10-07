from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Dict, Generator, Iterable, List

import pyodbc

from .config import Settings, get_settings

logger = logging.getLogger(__name__)


class Database:
    """Simple database accessor that opens ODBC connections on demand."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @contextmanager
    def connection(self) -> Generator[pyodbc.Connection, None, None]:
        """Yield a live pyodbc connection."""
        conn_str = self.settings.connection_string()
        conn = pyodbc.connect(conn_str, autocommit=True, timeout=10)
        try:
            yield conn
        finally:
            conn.close()

    def fetch_students(self, active_only: bool = False) -> List[Dict[str, object]]:
        """Fetch raw student rows from the configured query."""
        query = self._sanitized_query()
        if active_only and self.settings.active_where_clause:
            query = f"{query}\n{self.settings.active_where_clause}"

        logger.debug("Executing student query: %s", query)

        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [c[0].lower() for c in cursor.description]
            rows = cursor.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def fetch_student(self, reg_no: str) -> Dict[str, object] | None:
        """Fetch a single student record by registration number."""
        base_query = f"SELECT * FROM ({self._sanitized_query()}) AS source WHERE reg_no = ?"

        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(base_query, reg_no)
            row = cursor.fetchone()
            if not row:
                return None
            columns = [c[0].lower() for c in cursor.description]
            return dict(zip(columns, row))

    def _sanitized_query(self) -> str:
        """Return the main query without a trailing semicolon."""
        query = self.settings.students_query.strip()
        while query.endswith(";"):
            query = query[:-1].strip()
        return query


def raw_rows_to_dicts(cursor, rows: Iterable) -> List[Dict[str, object]]:
    """Convert DB cursor rows into dictionaries keyed by lowercase column names."""
    columns = [c[0].lower() for c in cursor.description]
    return [dict(zip(columns, row)) for row in rows]
