"""Backend-branching behavior in brick_ttl_resolver when OFDD_STORAGE_BACKEND=selene.

Confirms the resolver short-circuits the rdflib path and queries Selene via
``build_column_map`` / ``list_equipment_types``. Uses httpx.MockTransport so
no live Selene is required; the module factory is patched to feed the
MockTransport-backed client.
"""

from __future__ import annotations

import httpx
import pytest

pytest.importorskip("pydantic_settings")

import openfdd_stack.platform.brick_ttl_resolver as resolver_mod
from openfdd_stack.platform.selene import SeleneClient


def _mock_selene(handler) -> SeleneClient:
    return SeleneClient(
        "http://selene.local:8080",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        owns_client=True,
    )


def _gql(rows: list[dict]) -> httpx.Response:
    return httpx.Response(
        200,
        json={"status": "00000", "message": "ok", "row_count": len(rows), "data": rows},
    )


def _force_selene(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OFDD_STORAGE_BACKEND", "selene")


def test_resolve_from_ttl_uses_selene_when_backend_is_selene(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    _force_selene(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        # The rdflib path would never call out to Selene — asserting we hit
        # the HTTP layer is enough to prove we branched.
        assert request.url.path == "/gql"
        return _gql(
            [
                {
                    "brick_type": "Supply_Air_Temperature_Sensor",
                    "fdd_input": None,
                    "display_name": "sat",
                    "name": "sat",
                },
            ]
        )

    client = _mock_selene(handler)
    monkeypatch.setattr(resolver_mod, "_selene_client", lambda: client)

    # TTL path does not exist — must be ignored on the Selene branch.
    mapping = resolver_mod.resolve_from_ttl(tmp_path / "does-not-exist.ttl")
    assert mapping == {"Supply_Air_Temperature_Sensor": "sat"}


def test_get_equipment_types_uses_selene_when_backend_is_selene(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    _force_selene(monkeypatch)

    def handler(_request: httpx.Request) -> httpx.Response:
        return _gql([{"equipment_type": "AHU"}, {"equipment_type": "VAV"}])

    client = _mock_selene(handler)
    monkeypatch.setattr(resolver_mod, "_selene_client", lambda: client)

    types = resolver_mod.get_equipment_types_from_ttl(tmp_path / "nope.ttl")
    assert types == ["AHU", "VAV"]


def test_resolve_from_ttl_returns_empty_when_selene_client_unavailable(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    """Factory may return None on misconfigured URL / creds — must degrade gracefully."""
    _force_selene(monkeypatch)
    monkeypatch.setattr(resolver_mod, "_selene_client", lambda: None)

    assert resolver_mod.resolve_from_ttl(tmp_path / "nope.ttl") == {}


def test_get_equipment_types_returns_empty_when_selene_client_unavailable(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    _force_selene(monkeypatch)
    monkeypatch.setattr(resolver_mod, "_selene_client", lambda: None)

    assert resolver_mod.get_equipment_types_from_ttl(tmp_path / "nope.ttl") == []


def test_column_map_resolver_delegates_without_checking_ttl_existence(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    """BrickTtlColumnMapResolver must skip the ttl_path.exists() guard in selene mode."""
    _force_selene(monkeypatch)

    def handler(_request: httpx.Request) -> httpx.Response:
        return _gql(
            [
                {
                    "brick_type": "Outside_Air_Temperature_Sensor",
                    "fdd_input": None,
                    "display_name": "oat",
                    "name": "oat",
                },
            ]
        )

    client = _mock_selene(handler)
    monkeypatch.setattr(resolver_mod, "_selene_client", lambda: client)

    out = resolver_mod.BrickTtlColumnMapResolver().build_column_map(
        ttl_path=tmp_path / "missing.ttl"
    )
    assert out == {"Outside_Air_Temperature_Sensor": "oat"}


def test_timescale_backend_still_uses_rdflib(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Default (timescale) path must remain unchanged."""
    monkeypatch.setenv("OFDD_STORAGE_BACKEND", "timescale")
    pytest.importorskip("rdflib")

    ttl = tmp_path / "m.ttl"
    ttl.write_text("""
@prefix brick: <https://brickschema.org/schema/Brick#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://openfdd.local/point/sat> a brick:Supply_Air_Temperature_Sensor ;
    rdfs:label "sat" .
""")
    mapping = resolver_mod.resolve_from_ttl(ttl)
    assert mapping.get("Supply_Air_Temperature_Sensor") == "sat"
