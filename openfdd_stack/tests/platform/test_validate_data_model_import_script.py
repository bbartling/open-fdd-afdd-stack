import json
import subprocess
import sys


def _script_path() -> str:
    from pathlib import Path

    return str(Path(__file__).resolve().parents[3] / "scripts" / "validate_data_model_import.py")


def test_validate_data_model_import_script_accepts_valid_payload(tmp_path):
    payload = {
        "points": [
            {
                "point_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                "brick_type": "Supply_Air_Temperature_Sensor",
                "rule_input": "sat",
            }
        ]
    }
    payload_file = tmp_path / "valid-import.json"
    payload_file.write_text(json.dumps(payload), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, _script_path(), str(payload_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "VALID:" in proc.stdout


def test_validate_data_model_import_script_reports_validation_path(tmp_path):
    payload = {
        "points": [
            {
                "point_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                "unknown_key": "x",
            }
        ]
    }
    payload_file = tmp_path / "invalid-import.json"
    payload_file.write_text(json.dumps(payload), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, _script_path(), str(payload_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert "points[0].unknown_key" in proc.stdout
