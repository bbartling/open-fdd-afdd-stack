"""Unit tests for modbus_point_config.normalize_modbus_config."""

from openfdd_stack.platform.modbus_point_config import normalize_modbus_config


def test_normalize_minimal():
    n = normalize_modbus_config({"host": "10.0.0.1", "address": 100})
    assert n is not None
    assert n["host"] == "10.0.0.1"
    assert n["address"] == 100
    assert n["port"] == 502
    assert n["unit_id"] == 1
    assert n["function"] == "holding"
    assert n["count"] == 1


def test_normalize_rejects_bad_port():
    assert normalize_modbus_config({"host": "h", "address": 0, "port": 0}) is None
    assert normalize_modbus_config({"host": "h", "address": 0, "port": 70000}) is None


def test_normalize_rejects_bad_decode():
    assert normalize_modbus_config({"host": "h", "address": 0, "decode": "nope"}) is None


def test_normalize_coerces_float32_decode():
    n = normalize_modbus_config(
        {"host": "h", "address": 0, "count": 2, "function": "input", "decode": "float32"}
    )
    assert n is not None
    assert n["decode"] == "float32"
