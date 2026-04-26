"""CSV upload/validation API."""

from __future__ import annotations

import io

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field, ValidationError

from openfdd_stack.platform.drivers.csv_driver import (
    ingest_csv_dataframe,
    validate_csv_dataframe,
)

router = APIRouter(prefix="/csv", tags=["csv"])


class CsvUploadForm(BaseModel):
    site_id: str = Field(..., min_length=1, description="Site name or UUID")
    create_points: bool = Field(
        True, description="When true, upload can auto-create missing CSV points"
    )
    source_name: str | None = Field(
        None, description="Optional source label used for point external_id prefixes"
    )
    dry_run: bool = Field(
        False, description="When true, only validate and return preview metadata"
    )


@router.post("/upload", summary="Upload CSV, validate schema, and ingest")
async def upload_csv(
    file: UploadFile = File(...),
    site_id: str = Form(...),
    create_points: bool = Form(True),
    source_name: str | None = Form(None),
    dry_run: bool = Form(False),
):
    try:
        form = CsvUploadForm(
            site_id=site_id,
            create_points=create_points,
            source_name=source_name,
            dry_run=dry_run,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "CSV_FORM_VALIDATION_ERROR",
                "message": "CSV upload form validation failed",
                "details": {"errors": e.errors()},
            },
        ) from e

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="CSV must be UTF-8 encoded",
        ) from None

    try:
        import pandas as pd

        df = pd.read_csv(io.StringIO(text))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}") from e

    validation = validate_csv_dataframe(df)
    if validation["errors"]:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "CSV_VALIDATION_ERROR",
                "message": "CSV validation failed",
                "details": {
                    "errors": validation["errors"],
                    "timestamp_column": validation.get("timestamp_column"),
                },
            },
        )

    preview = {
        "rows_total": int(validation["rows_total"]),
        "rows_with_valid_timestamp": int(validation["rows_with_valid_timestamp"]),
        "timestamp_column": validation.get("timestamp_column"),
        "metric_columns": validation.get("metric_columns", []),
    }
    if form.dry_run:
        return {"ok": True, "validated": True, "preview": preview}

    result = ingest_csv_dataframe(
        site_id=form.site_id,
        df=df,
        source_name=form.source_name or file.filename or "uploaded",
        create_points=form.create_points,
    )
    return {"ok": True, "validated": True, "preview": preview, "ingest": result}
