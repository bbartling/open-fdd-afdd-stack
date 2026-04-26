from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from openfdd_stack.platform.api.main import app

client = TestClient(app)


def test_csv_upload_rejects_missing_timestamp_column():
    csv_text = "value_a,value_b\n1,2\n3,4\n"
    r = client.post(
        "/csv/upload",
        files={"file": ("bad.csv", csv_text, "text/csv")},
        data={"site_id": "csv-upload", "create_points": "true"},
    )
    assert r.status_code == 422
    payload = r.json()
    assert payload["error"]["code"] == "CSV_VALIDATION_ERROR"
    assert "Missing timestamp column" in payload["error"]["details"]["errors"][0]


def test_csv_upload_success_uses_ingest_helper():
    csv_text = "timestamp,val\n2026-04-01T00:00:00Z,1.2\n"
    with patch(
        "openfdd_stack.platform.api.csv_ingest.ingest_csv_dataframe",
        return_value={"rows_inserted": 1, "points_upserted": 1},
    ):
        r = client.post(
            "/csv/upload",
            files={"file": ("ok.csv", csv_text, "text/csv")},
            data={"site_id": "csv-upload", "create_points": "true"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["ingest"]["rows_inserted"] == 1
