"""Brick → column_map and equipment-type resolver for the AFDD platform.

Two backends, selected by ``OFDD_STORAGE_BACKEND``:

- ``timescale`` (default): SPARQL over the unified ``config/data_model.ttl``
  via ``rdflib``. Pre-Selene behavior, unchanged.
- ``selene``: GQL against the live SeleneDB graph via
  :mod:`openfdd_stack.platform.selene.column_map`. No TTL file read.

The ``open-fdd`` engine package stays RDF-free; this module (and the Selene
helper it delegates to) are stack-only. rdflib is imported lazily so the
Selene path does not pay the import cost.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Union

from openfdd_stack.platform.config import is_selene_backend

logger = logging.getLogger(__name__)


def _selene_client():
    """Lazily build a ``SeleneClient`` from platform settings.

    Returns ``None`` on any construction error (bad URL, missing creds) so
    the caller can fall back to an empty map without blowing up boot.
    """
    try:
        from openfdd_stack.platform.selene import make_selene_client_from_settings

        return make_selene_client_from_settings()
    except Exception:  # noqa: BLE001
        logger.warning("selene client construction failed", exc_info=True)
        return None


def resolve_from_ttl(ttl_path: Union[str, Path]) -> Dict[str, str]:
    """Return ``{brick_class | fdd_input: column_name}``.

    When ``OFDD_STORAGE_BACKEND=selene`` the ``ttl_path`` argument is ignored
    and the map is built from Selene's graph. Otherwise SPARQL over the TTL
    file is used (legacy rdflib path).

    For the Selene path, ``fdd_input`` disambiguates multiple points sharing
    the same Brick class, identical to the TTL path's ``ofdd:mapsToRuleInput``
    semantics.
    """
    if is_selene_backend():
        from openfdd_stack.platform.selene.column_map import build_column_map

        client = _selene_client()
        if client is None:
            return {}
        with client:
            return build_column_map(client)

    try:
        from rdflib import Graph
    except ImportError as e:
        raise ImportError(
            "rdflib required for Brick TTL resolution. Install openfdd-afdd-stack "
            "dependencies or: pip install rdflib"
        ) from e

    g = Graph()
    g.parse(ttl_path, format="turtle")
    mapping: Dict[str, str] = {}

    q = """
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    PREFIX ofdd: <http://openfdd.local/ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?brick_class ?label ?rule_input WHERE {
        ?point a ?brick_type .
        FILTER(STRSTARTS(STR(?brick_type), STR(brick:)))
        BIND(REPLACE(STR(?brick_type), "https://brickschema.org/schema/Brick#", "") AS ?brick_class)
        ?point rdfs:label ?label .
        OPTIONAL { ?point ofdd:mapsToRuleInput ?rule_input . }
    }
    """
    rows = list(g.query(q))

    brick_counts: Dict[str, int] = {}
    for row in rows:
        bc = str(row.brick_class)
        brick_counts[bc] = brick_counts.get(bc, 0) + 1

    for row in rows:
        brick_class = str(row.brick_class)
        label = str(row.label).strip('"')
        rule_input = (
            str(row.rule_input).strip('"')
            if row.rule_input and str(row.rule_input).strip()
            else None
        )

        if brick_counts[brick_class] > 1 and rule_input:
            key = f"{brick_class}|{rule_input}"
        else:
            key = brick_class
        mapping[key] = label

        if rule_input:
            mapping[rule_input] = label

    return mapping


def get_equipment_types_from_ttl(ttl_path: Union[str, Path]) -> list:
    """Return distinct equipment types (e.g. ``["VAV_AHU", "AHU"]``).

    When ``OFDD_STORAGE_BACKEND=selene`` the ``ttl_path`` argument is ignored
    and the list is queried from Selene. Used to filter which rules apply
    to the equipment in the data model.
    """
    if is_selene_backend():
        from openfdd_stack.platform.selene.column_map import list_equipment_types

        client = _selene_client()
        if client is None:
            return []
        with client:
            return list_equipment_types(client)

    try:
        from rdflib import Graph
    except ImportError as e:
        raise ImportError(
            "rdflib required for Brick TTL resolution. Install openfdd-afdd-stack "
            "dependencies or: pip install rdflib"
        ) from e

    g = Graph()
    g.parse(ttl_path, format="turtle")
    types = []
    q = """
    PREFIX ofdd: <http://openfdd.local/ontology#>
    SELECT DISTINCT ?equipmentType WHERE {
        ?equipment ofdd:equipmentType ?equipmentType .
    }
    """
    for row in g.query(q):
        t = str(row.equipmentType).strip('"')
        if t and t not in types:
            types.append(t)
    return types


class BrickTtlColumnMapResolver:
    """Default stack resolver — satisfies
    :class:`open_fdd.engine.column_map_resolver.ColumnMapResolver`.

    Plugged into ``run_fdd_loop`` / ``RulesLoader``. When Selene is the
    backend, ``ttl_path`` is ignored and the map is read from the graph.
    """

    def build_column_map(self, *, ttl_path: Path) -> Dict[str, str]:
        if is_selene_backend():
            return dict(resolve_from_ttl(ttl_path))
        if ttl_path.exists():
            return dict(resolve_from_ttl(str(ttl_path)))
        return {}
