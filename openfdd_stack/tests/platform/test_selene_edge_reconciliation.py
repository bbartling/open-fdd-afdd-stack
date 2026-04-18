"""Edge reconciliation tests for Phase 2.3d.

``_reconcile_single_edge`` is the shared helper that keeps FK columns and
graph edges in sync. These tests exercise its behaviour directly and via
``upsert_equipment`` / ``upsert_point`` end-to-end.

Conventions:
- ``(:site)-[:contains]->(:equipment)-[:contains]->(:point)`` hierarchy
- ``(:equipment)-[:feeds]->(:equipment)`` flow (both feeds/fed_by Postgres
  columns route to this one edge label, just different directions).
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from openfdd_stack.platform.selene import (
    EQUIPMENT_LABEL,
    EXTERNAL_ID_PROP,
    POINT_LABEL,
    SITE_LABEL,
    SeleneClient,
    upsert_equipment,
    upsert_point,
)


def _mock_client(handler) -> SeleneClient:
    # owns_client=True so the context-manager exit tears down the
    # MockTransport-backed httpx.Client in one step \u2014 keeps the test suite
    # from leaking clients across runs.
    return SeleneClient(
        "http://selene.local:8080",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        owns_client=True,
    )


class _FakeGraph:
    """Minimal in-memory graph for testing edge reconciliation end-to-end.

    Tracks nodes and edges so the MockTransport handler can answer
    GET /nodes, POST /nodes, PUT /nodes/{id}, GET /nodes/{id}/edges,
    POST /edges, DELETE /edges/{id} with realistic state transitions.
    """

    def __init__(self) -> None:
        self.nodes: dict[int, dict[str, Any]] = {}
        self.edges: dict[int, dict[str, Any]] = {}
        self._next_node = 1
        self._next_edge = 1

    def seed_node(self, label: str, external_id: str, **extras: Any) -> int:
        nid = self._next_node
        self._next_node += 1
        self.nodes[nid] = {
            "id": nid,
            "labels": [label],
            "properties": {EXTERNAL_ID_PROP: external_id, **extras},
        }
        return nid

    def handler(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        method = request.method

        if method == "GET" and path == "/nodes":
            label = request.url.params.get("label")
            matching = [
                n for n in self.nodes.values() if label is None or label in n["labels"]
            ]
            return httpx.Response(200, json={"nodes": matching, "total": len(matching)})
        if method == "POST" and path == "/nodes":
            body = json.loads(request.content)
            nid = self._next_node
            self._next_node += 1
            self.nodes[nid] = {
                "id": nid,
                "labels": body["labels"],
                "properties": body.get("properties", {}),
            }
            return httpx.Response(201, json=self.nodes[nid])
        if method == "PUT" and path.startswith("/nodes/"):
            nid = int(path.rsplit("/", 1)[-1])
            body = json.loads(request.content)
            props = dict(self.nodes[nid].get("properties", {}))
            props.update(body.get("set_properties", {}))
            for k in body.get("remove_properties") or []:
                props.pop(k, None)
            self.nodes[nid]["properties"] = props
            return httpx.Response(200, json=self.nodes[nid])
        if method == "GET" and path.startswith("/nodes/") and path.endswith("/edges"):
            nid = int(path.rsplit("/", 2)[-2])
            matching = [
                e
                for e in self.edges.values()
                if e["source"] == nid or e["target"] == nid
            ]
            return httpx.Response(
                200,
                json={"node_id": nid, "edges": matching, "total": len(matching)},
            )
        if method == "POST" and path == "/edges":
            body = json.loads(request.content)
            eid = self._next_edge
            self._next_edge += 1
            self.edges[eid] = {
                "id": eid,
                "source": body["source"],
                "target": body["target"],
                "label": body["label"],
                "properties": body.get("properties", {}),
            }
            return httpx.Response(201, json=self.edges[eid])
        if method == "DELETE" and path.startswith("/edges/"):
            eid = int(path.rsplit("/", 1)[-1])
            self.edges.pop(eid, None)
            return httpx.Response(204)
        raise AssertionError(f"unexpected {method} {path}")


# ---------------------------------------------------------------------------
# site -> equipment contains edge
# ---------------------------------------------------------------------------


def test_upsert_equipment_creates_contains_edge_from_site():
    g = _FakeGraph()
    site_nid = g.seed_node(SITE_LABEL, "site-1", name="hq")

    with _mock_client(g.handler) as client:
        upsert_equipment(
            client,
            {"id": "eq-1", "site_id": "site-1", "name": "AHU-1"},
        )

    contains_edges = [e for e in g.edges.values() if e["label"] == "contains"]
    assert len(contains_edges) == 1
    edge = contains_edges[0]
    assert edge["source"] == site_nid  # site contains equipment
    assert g.nodes[edge["target"]]["properties"][EXTERNAL_ID_PROP] == "eq-1"


def test_upsert_equipment_moves_contains_edge_when_site_id_changes():
    g = _FakeGraph()
    site_a = g.seed_node(SITE_LABEL, "site-a")
    site_b = g.seed_node(SITE_LABEL, "site-b")

    with _mock_client(g.handler) as client:
        upsert_equipment(client, {"id": "eq-1", "site_id": "site-a", "name": "AHU-1"})
        # Move to site-b
        upsert_equipment(client, {"id": "eq-1", "site_id": "site-b", "name": "AHU-1"})

    contains_edges = [e for e in g.edges.values() if e["label"] == "contains"]
    assert len(contains_edges) == 1
    assert contains_edges[0]["source"] == site_b


def test_upsert_equipment_drops_contains_edge_when_site_id_cleared():
    """Setting site_id to None should remove the contains edge (rare but supported)."""
    g = _FakeGraph()
    g.seed_node(SITE_LABEL, "site-a")

    with _mock_client(g.handler) as client:
        upsert_equipment(client, {"id": "eq-1", "site_id": "site-a", "name": "AHU-1"})
        upsert_equipment(client, {"id": "eq-1", "site_id": None, "name": "AHU-1"})

    contains_edges = [e for e in g.edges.values() if e["label"] == "contains"]
    assert contains_edges == []


def test_upsert_equipment_skips_contains_edge_when_site_not_yet_synced():
    """Edge creation waits when the parent site isn't in Selene yet (backfill order)."""
    g = _FakeGraph()

    with _mock_client(g.handler) as client:
        upsert_equipment(
            client, {"id": "eq-1", "site_id": "unknown-site", "name": "AHU-1"}
        )

    # Node created, no edges (site absent)
    assert any(
        n["properties"].get(EXTERNAL_ID_PROP) == "eq-1" for n in g.nodes.values()
    )
    assert [e for e in g.edges.values() if e["label"] == "contains"] == []


# ---------------------------------------------------------------------------
# equipment feeds equipment
# ---------------------------------------------------------------------------


def test_upsert_equipment_creates_feeds_edge_outgoing():
    g = _FakeGraph()
    g.seed_node(EQUIPMENT_LABEL, "vav-1", name="vav-1")

    with _mock_client(g.handler) as client:
        upsert_equipment(
            client,
            {
                "id": "ahu-1",
                "site_id": None,
                "name": "AHU-1",
                "feeds_equipment_id": "vav-1",
            },
        )

    feeds = [e for e in g.edges.values() if e["label"] == "feeds"]
    assert len(feeds) == 1
    assert g.nodes[feeds[0]["source"]]["properties"][EXTERNAL_ID_PROP] == "ahu-1"
    assert g.nodes[feeds[0]["target"]]["properties"][EXTERNAL_ID_PROP] == "vav-1"


def test_upsert_equipment_creates_feeds_edge_incoming_from_fed_by():
    """fed_by_equipment_id=X on A means X feeds A \u2014 incoming feeds edge."""
    g = _FakeGraph()
    g.seed_node(EQUIPMENT_LABEL, "ahu-upstream", name="ahu-upstream")

    with _mock_client(g.handler) as client:
        upsert_equipment(
            client,
            {
                "id": "vav-1",
                "site_id": None,
                "name": "VAV-1",
                "fed_by_equipment_id": "ahu-upstream",
            },
        )

    feeds = [e for e in g.edges.values() if e["label"] == "feeds"]
    assert len(feeds) == 1
    assert g.nodes[feeds[0]["source"]]["properties"][EXTERNAL_ID_PROP] == "ahu-upstream"
    assert g.nodes[feeds[0]["target"]]["properties"][EXTERNAL_ID_PROP] == "vav-1"


def test_upsert_equipment_both_feeds_columns_produce_two_distinct_edges():
    """feeds_id=Down + fed_by_id=Up yields two separate feeds edges (outgoing + incoming)."""
    g = _FakeGraph()
    g.seed_node(EQUIPMENT_LABEL, "upstream")
    g.seed_node(EQUIPMENT_LABEL, "downstream")

    with _mock_client(g.handler) as client:
        upsert_equipment(
            client,
            {
                "id": "middle",
                "site_id": None,
                "name": "middle",
                "feeds_equipment_id": "downstream",
                "fed_by_equipment_id": "upstream",
            },
        )

    feeds = [e for e in g.edges.values() if e["label"] == "feeds"]
    assert len(feeds) == 2
    middle_external = "middle"
    middle_id = next(
        n["id"]
        for n in g.nodes.values()
        if n["properties"].get(EXTERNAL_ID_PROP) == middle_external
    )
    # one outgoing, one incoming
    assert any(e["source"] == middle_id for e in feeds)
    assert any(e["target"] == middle_id for e in feeds)


# ---------------------------------------------------------------------------
# equipment -> point contains
# ---------------------------------------------------------------------------


def test_upsert_point_creates_contains_edge_from_equipment_when_set():
    g = _FakeGraph()
    eq_nid = g.seed_node(EQUIPMENT_LABEL, "eq-1", name="ahu-1")
    g.seed_node(SITE_LABEL, "site-1", name="hq")

    with _mock_client(g.handler) as client:
        upsert_point(
            client,
            {
                "id": "p-1",
                "site_id": "site-1",
                "equipment_id": "eq-1",
                "external_id": "sa-temp",
            },
        )

    contains = [e for e in g.edges.values() if e["label"] == "contains"]
    assert len(contains) == 1
    assert contains[0]["source"] == eq_nid  # equipment -> point, NOT site -> point


def test_upsert_point_creates_contains_edge_from_site_when_equipment_null():
    """Points without equipment_id parent to the site directly."""
    g = _FakeGraph()
    site_nid = g.seed_node(SITE_LABEL, "site-1")

    with _mock_client(g.handler) as client:
        upsert_point(
            client,
            {
                "id": "p-1",
                "site_id": "site-1",
                "equipment_id": None,
                "external_id": "site-meter",
            },
        )

    contains = [e for e in g.edges.values() if e["label"] == "contains"]
    assert len(contains) == 1
    assert contains[0]["source"] == site_nid


def test_upsert_point_moves_contains_edge_when_equipment_changes():
    g = _FakeGraph()
    eq_a = g.seed_node(EQUIPMENT_LABEL, "eq-a")
    eq_b = g.seed_node(EQUIPMENT_LABEL, "eq-b")
    g.seed_node(SITE_LABEL, "site-1")

    with _mock_client(g.handler) as client:
        upsert_point(
            client,
            {
                "id": "p-1",
                "site_id": "site-1",
                "equipment_id": "eq-a",
                "external_id": "p",
            },
        )
        upsert_point(
            client,
            {
                "id": "p-1",
                "site_id": "site-1",
                "equipment_id": "eq-b",
                "external_id": "p",
            },
        )

    contains = [e for e in g.edges.values() if e["label"] == "contains"]
    assert len(contains) == 1
    assert contains[0]["source"] == eq_b


def test_reconcile_single_edge_rejects_invalid_direction():
    """Guards against silent miswiring on a typo like 'incomming'."""
    from openfdd_stack.platform.selene.graph_crud import _reconcile_single_edge

    g = _FakeGraph()
    g.seed_node(SITE_LABEL, "site-1")
    with _mock_client(g.handler) as client:
        with pytest.raises(ValueError, match="direction"):
            _reconcile_single_edge(
                client,
                source_id=1,
                edge_label="contains",
                direction="incomming",  # typo
                target_label=SITE_LABEL,
                target_external_id="site-1",
                op_name="test",
            )


def test_reconcile_logs_edge_delete_failures(caplog):
    """When delete_edge raises, the failure must surface in logs (not a silent pass)."""
    g = _FakeGraph()
    site_a = g.seed_node(SITE_LABEL, "site-a")
    site_b = g.seed_node(SITE_LABEL, "site-b")

    # First upsert creates the initial contains edge to site-a.
    with _mock_client(g.handler) as client:
        upsert_equipment(client, {"id": "eq-1", "site_id": "site-a", "name": "AHU-1"})

    # Now make DELETE /edges/{id} fail. The move to site-b triggers a stale
    # edge delete; we expect a WARNING to land in caplog.
    class _FailingDeleteGraph(_FakeGraph):
        def __init__(self, seed):
            super().__init__()
            self.nodes = dict(seed.nodes)
            self.edges = dict(seed.edges)
            self._next_node = seed._next_node
            self._next_edge = seed._next_edge

        def handler(self, request):
            if request.method == "DELETE" and request.url.path.startswith("/edges/"):
                return httpx.Response(500, json={"error": "simulated"})
            return super().handler(request)

    failing = _FailingDeleteGraph(g)
    with _mock_client(failing.handler) as client:
        with caplog.at_level("WARNING"):
            upsert_equipment(
                client, {"id": "eq-1", "site_id": "site-b", "name": "AHU-1"}
            )
    assert any(
        "failed to delete stale edge" in rec.message for rec in caplog.records
    )


def test_upsert_point_is_idempotent_on_repeated_upsert():
    """Running the same upsert twice creates one node and one edge, not duplicates."""
    g = _FakeGraph()
    g.seed_node(EQUIPMENT_LABEL, "eq-1")
    g.seed_node(SITE_LABEL, "site-1")

    row = {
        "id": "p-1",
        "site_id": "site-1",
        "equipment_id": "eq-1",
        "external_id": "p",
    }
    with _mock_client(g.handler) as client:
        upsert_point(client, row)
        upsert_point(client, row)

    points = [n for n in g.nodes.values() if POINT_LABEL in n["labels"]]
    assert len(points) == 1
    contains = [e for e in g.edges.values() if e["label"] == "contains"]
    assert len(contains) == 1
