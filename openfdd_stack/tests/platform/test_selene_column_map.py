"""Unit tests for the Selene-backed column_map and equipment-type resolvers.

Uses httpx.MockTransport so the tests never touch a live Selene. The tests
assert shape parity with the TTL/rdflib resolver (see
``test_brick_ttl_resolver.py``) — the same inputs must yield the same
``{brick_class[|fdd_input]: column_name}`` shape.
"""

from __future__ import annotations

from typing import Any

import httpx

from openfdd_stack.platform.selene import SeleneClient
from openfdd_stack.platform.selene.column_map import (
    build_column_map,
    list_equipment_types,
)


def _mock_client(handler) -> SeleneClient:
    return SeleneClient(
        "http://selene.local:8080",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        owns_client=True,
    )


def _gql_response(rows: list[dict[str, Any]]) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "status": "00000",
            "message": "Success",
            "row_count": len(rows),
            "data": rows,
        },
    )


# ---------------------------------------------------------------------------
# build_column_map
# ---------------------------------------------------------------------------


def test_build_column_map_returns_empty_when_graph_empty():
    def handler(_request: httpx.Request) -> httpx.Response:
        return _gql_response([])

    with _mock_client(handler) as client:
        assert build_column_map(client) == {}


def test_build_column_map_unique_brick_types_keyed_by_brick_class():
    rows = [
        {
            "brick_type": "Supply_Air_Temperature_Sensor",
            "fdd_input": None,
            "display_name": "sat",
            "name": "sat",
        },
        {
            "brick_type": "Outside_Air_Temperature_Sensor",
            "fdd_input": None,
            "display_name": "oat",
            "name": "oat",
        },
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/gql"
        return _gql_response(rows)

    with _mock_client(handler) as client:
        mapping = build_column_map(client)
    assert mapping == {
        "Supply_Air_Temperature_Sensor": "sat",
        "Outside_Air_Temperature_Sensor": "oat",
    }


def test_build_column_map_disambiguates_duplicates_with_fdd_input():
    """Matches rdflib behavior: dup Brick class + rule_input → 'Brick|rule_input'."""
    rows = [
        {
            "brick_type": "Valve_Command",
            "fdd_input": "reheat",
            "display_name": "v_cmd_1",
            "name": "v-cmd-1",
        },
        {
            "brick_type": "Valve_Command",
            "fdd_input": "cooling",
            "display_name": "v_cmd_2",
            "name": "v-cmd-2",
        },
    ]

    def handler(_request: httpx.Request) -> httpx.Response:
        return _gql_response(rows)

    with _mock_client(handler) as client:
        mapping = build_column_map(client)

    assert mapping["Valve_Command|reheat"] == "v_cmd_1"
    assert mapping["Valve_Command|cooling"] == "v_cmd_2"
    # top-level fdd_input alias always added so rules can key by either name
    assert mapping["reheat"] == "v_cmd_1"
    assert mapping["cooling"] == "v_cmd_2"
    # plain Brick class is not a key when duplicates exist
    assert "Valve_Command" not in mapping


def test_build_column_map_falls_back_to_name_when_display_name_missing():
    """display_name is None when the BAS value was already canonical."""
    rows = [
        {
            "brick_type": "Return_Air_Temperature_Sensor",
            "fdd_input": None,
            "display_name": None,
            "name": "rat",
        },
    ]

    def handler(_request: httpx.Request) -> httpx.Response:
        return _gql_response(rows)

    with _mock_client(handler) as client:
        mapping = build_column_map(client)
    assert mapping == {"Return_Air_Temperature_Sensor": "rat"}


def test_build_column_map_skips_row_with_no_column_name():
    """A point missing both display_name and name is unmappable."""
    rows = [
        {
            "brick_type": "Supply_Air_Temperature_Sensor",
            "fdd_input": None,
            "display_name": None,
            "name": None,
        },
        {
            "brick_type": "Outside_Air_Temperature_Sensor",
            "fdd_input": None,
            "display_name": "oat",
            "name": "oat",
        },
    ]

    def handler(_request: httpx.Request) -> httpx.Response:
        return _gql_response(rows)

    with _mock_client(handler) as client:
        mapping = build_column_map(client)
    assert mapping == {"Outside_Air_Temperature_Sensor": "oat"}


def test_build_column_map_row_without_brick_type_still_emits_fdd_input_alias():
    """A point with only fdd_input (no Brick class) still routes by rule_input."""
    rows = [
        {
            "brick_type": None,
            "fdd_input": "reheat",
            "display_name": "v_reheat",
            "name": "v-reheat",
        },
    ]

    def handler(_request: httpx.Request) -> httpx.Response:
        return _gql_response(rows)

    with _mock_client(handler) as client:
        mapping = build_column_map(client)
    assert mapping == {"reheat": "v_reheat"}


def test_build_column_map_returns_empty_on_selene_error():
    """Selene errors degrade gracefully — boot must not fail."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    with _mock_client(handler) as client:
        assert build_column_map(client) == {}


# ---------------------------------------------------------------------------
# list_equipment_types
# ---------------------------------------------------------------------------


def test_list_equipment_types_returns_distinct_values():
    rows = [
        {"equipment_type": "AHU"},
        {"equipment_type": "VAV"},
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/gql"
        return _gql_response(rows)

    with _mock_client(handler) as client:
        types = list_equipment_types(client)
    assert types == ["AHU", "VAV"]


def test_list_equipment_types_dedupes_if_server_doesnt():
    """Belt-and-braces: even if DISTINCT is lost, client-side dedup holds."""
    rows = [
        {"equipment_type": "AHU"},
        {"equipment_type": "VAV"},
        {"equipment_type": "AHU"},
    ]

    def handler(_request: httpx.Request) -> httpx.Response:
        return _gql_response(rows)

    with _mock_client(handler) as client:
        types = list_equipment_types(client)
    assert types == ["AHU", "VAV"]


def test_list_equipment_types_skips_empty_and_whitespace_values():
    rows = [
        {"equipment_type": "AHU"},
        {"equipment_type": ""},
        {"equipment_type": "   "},
        {"equipment_type": "VAV"},
    ]

    def handler(_request: httpx.Request) -> httpx.Response:
        return _gql_response(rows)

    with _mock_client(handler) as client:
        types = list_equipment_types(client)
    assert types == ["AHU", "VAV"]


def test_list_equipment_types_returns_empty_on_selene_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    with _mock_client(handler) as client:
        assert list_equipment_types(client) == []
