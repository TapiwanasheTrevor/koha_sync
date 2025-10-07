from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query

from .config import Settings, get_settings
from .db import Database
from .mapping import to_koha_patron

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

settings: Settings = get_settings()
database = Database(settings)

app = FastAPI(
    title="Pastel → Koha JSON Bridge",
    version="0.1.0",
    summary="Expose student records as JSON for Koha integration.",
)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Simple readiness probe."""
    return {"status": "ok"}


@app.get("/students")
async def list_students(
    active_only: bool = Query(False, description="Append ACTIVE_WHERE_CLAUSE when true"),
) -> Dict[str, Any]:
    """Return raw student records from the source database."""
    rows = database.fetch_students(active_only=active_only)
    return {"count": len(rows), "data": rows}


@app.get("/students/{reg_no}")
async def get_student(reg_no: str) -> Dict[str, Any]:
    """Return a single raw student record."""
    record = database.fetch_student(reg_no)
    if not record:
        raise HTTPException(status_code=404, detail=f"Student with reg_no '{reg_no}' not found")
    return record


@app.get("/koha/patrons")
async def list_patrons(
    active_only: bool = Query(False, description="Append ACTIVE_WHERE_CLAUSE when true"),
    include_raw: bool = Query(False, description="Include original record alongside Koha payload."),
    strict: bool = Query(False, description="Fail when a record is missing required fields."),
) -> Dict[str, Any]:
    rows = database.fetch_students(active_only=active_only)

    patrons: List[Any] = []
    skipped: List[Dict[str, Any]] = []

    for row in rows:
        try:
            payload = to_koha_patron(row, settings)
        except KeyError as exc:
            message = str(exc)
            logger.warning("Skipping record due to missing fields: %s (reg_no=%s)", message, row.get("reg_no"))
            skipped.append({"reg_no": row.get("reg_no"), "reason": message})
            if strict:
                raise HTTPException(status_code=500, detail=message)
            continue

        if include_raw:
            patrons.append({"koha": payload, "raw": row})
        else:
            patrons.append(payload)

    response: Dict[str, Any] = {"count": len(patrons), "data": patrons}
    if skipped:
        response["skipped"] = skipped
    return response


@app.get("/koha/patrons/{reg_no}")
async def get_patron(
    reg_no: str,
    include_raw: bool = Query(False, description="Include original record alongside Koha payload."),
) -> Dict[str, Any]:
    record = database.fetch_student(reg_no)
    if not record:
        raise HTTPException(status_code=404, detail=f"Student with reg_no '{reg_no}' not found")

    payload = to_koha_patron(record, settings)
    if include_raw:
        return {"koha": payload, "raw": record}
    return payload


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("koha_sync.app:app", host=settings.host, port=settings.port, reload=False)
