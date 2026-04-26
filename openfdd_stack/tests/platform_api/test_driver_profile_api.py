from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from openfdd_stack.platform.api.main import app

client = TestClient(app)


def test_driver_profile_endpoint_returns_status(tmp_path):
    with patch(
        "openfdd_stack.platform.api.config.load_driver_profile",
        return_value=(
            {
                "bacnet": True,
                "fdd": True,
                "weather": True,
                "onboard": False,
                "csv": True,
                "host_stats": True,
            },
            tmp_path / "drivers.yaml",
            True,
        ),
    ):
        r = client.get("/config/driver-profile")
    assert r.status_code == 200
    body = r.json()
    assert body["drivers"]["csv"] is True
    assert body["services"]["csv-scraper"] is True
    assert body["services"]["onboard-scraper"] is False
