"""Timeseries API tests for latest and purge helpers."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from openfdd_stack.platform.api.main import app

client = TestClient(app)


def _mock_conn_with_cursor(*, rowcount: int = 0):
    conn = MagicMock()
    cur = MagicMock()
    cur.rowcount = rowcount
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=None)
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=None)
    return conn, cur


def test_timeseries_purge_all_deletes_rows():
    conn, cur = _mock_conn_with_cursor(rowcount=42)
    with patch("openfdd_stack.platform.api.timeseries.get_conn", return_value=conn):
        r = client.post("/timeseries/purge", json={})

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["scope"] == "all"
    assert body["deleted_rows"] == 42
    cur.execute.assert_called_once_with("DELETE FROM timeseries_readings")


def test_timeseries_purge_site_deletes_site_rows_only():
    conn, cur = _mock_conn_with_cursor(rowcount=7)
    cur.fetchone.return_value = {"id": "11111111-1111-1111-1111-111111111111"}
    with patch("openfdd_stack.platform.api.timeseries.get_conn", return_value=conn):
        r = client.post("/timeseries/purge", json={"site_id": "default"})

    assert r.status_code == 200
    body = r.json()
    assert body["scope"] == "site"
    assert body["site_id"] == "11111111-1111-1111-1111-111111111111"
    assert body["deleted_rows"] == 7
    cur.execute.assert_any_call(
        "SELECT id::text AS id FROM sites WHERE id::text = %s OR name = %s LIMIT 1",
        ("default", "default"),
    )
    cur.execute.assert_any_call(
        "DELETE FROM timeseries_readings WHERE site_id = %s",
        ("11111111-1111-1111-1111-111111111111",),
    )


def test_timeseries_purge_404_when_site_missing():
    conn, cur = _mock_conn_with_cursor(rowcount=0)
    cur.fetchone.return_value = None
    with patch("openfdd_stack.platform.api.timeseries.get_conn", return_value=conn):
        r = client.post("/timeseries/purge", json={"site_id": "missing-site"})
    assert r.status_code == 404
    assert "No site found" in r.json()["error"]["message"]
