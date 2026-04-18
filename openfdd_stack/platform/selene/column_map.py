"""Selene-backed resolver for the FDD loop's Brick → column-name map.

The rdflib path in :mod:`openfdd_stack.platform.brick_ttl_resolver` parses
``config/data_model.ttl`` with SPARQL to build ``{brick_class: column_name}``
and a list of distinct ``equipment_type`` values. This module reproduces
that output by querying the SeleneDB graph — the same data written by
``upsert_point`` / ``upsert_equipment`` in :mod:`.graph_crud`.

Key convention (preserved for rule-YAML compatibility):

- Unique Brick class → ``{brick_class: column_name}``
- Duplicate Brick class with ``fdd_input`` disambiguator →
  ``{f"{brick_class}|{fdd_input}": column_name}``
- ``fdd_input`` value → ``{fdd_input: column_name}`` (rule-input shortcut)

``column_name`` is the BAS-native point identifier — ``display_name`` when set
(the original non-canonical name), otherwise ``name`` (the canonicalised form,
which matches the BAS value when no normalisation was needed).
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from openfdd_stack.platform.selene.client import SeleneClient
from openfdd_stack.platform.selene.exceptions import SeleneError
from openfdd_stack.platform.selene.graph_crud import EQUIPMENT_LABEL, POINT_LABEL

logger = logging.getLogger(__name__)


# Interpolating the shared label constants here prevents query drift if the
# canonical labels ever change — one place to update instead of two.
_POINT_QUERY = (
    f"MATCH (p:{POINT_LABEL}) "
    "RETURN p.brick_type AS brick_type, "
    "p.fdd_input AS fdd_input, "
    "p.display_name AS display_name, "
    "p.name AS name"
)

_EQUIPMENT_TYPES_QUERY = (
    f"MATCH (e:{EQUIPMENT_LABEL}) "
    "WHERE e.equipment_type IS NOT NULL "
    "RETURN DISTINCT e.equipment_type AS equipment_type"
)


def _row_str(row: dict[str, Any], key: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def build_column_map(client: SeleneClient) -> dict[str, str]:
    """Build ``{brick_class | fdd_input: column_name}`` by querying Selene.

    Mirrors ``resolve_from_ttl`` but sources the data from the live graph so
    the FDD loop no longer depends on a serialised TTL file. Returns ``{}``
    on any Selene error — boot must not fail just because the graph is
    momentarily unreachable; the loop will be re-tried on the next tick.
    """
    try:
        rows = client.gql_rows(_POINT_QUERY)
    except SeleneError:
        logger.warning("selene build_column_map failed", exc_info=True)
        return {}

    brick_counts: Counter[str] = Counter()
    for row in rows:
        bt = _row_str(row, "brick_type")
        if bt:
            brick_counts[bt] += 1

    mapping: dict[str, str] = {}
    for row in rows:
        brick_type = _row_str(row, "brick_type")
        fdd_input = _row_str(row, "fdd_input")
        column_name = _row_str(row, "display_name") or _row_str(row, "name")
        if not column_name:
            continue
        if brick_type:
            if brick_counts[brick_type] > 1 and fdd_input:
                mapping[f"{brick_type}|{fdd_input}"] = column_name
            else:
                mapping[brick_type] = column_name
        if fdd_input:
            mapping[fdd_input] = column_name
    return mapping


def list_equipment_types(client: SeleneClient) -> list[str]:
    """Return distinct ``equipment_type`` values, insertion-ordered by Selene.

    Mirrors ``get_equipment_types_from_ttl``. Returns ``[]`` on Selene error;
    the caller treats an empty list as "no equipment filter applied".
    """
    try:
        rows = client.gql_rows(_EQUIPMENT_TYPES_QUERY)
    except SeleneError:
        logger.warning("selene list_equipment_types failed", exc_info=True)
        return []

    out: list[str] = []
    seen: set[str] = set()
    for row in rows:
        et = _row_str(row, "equipment_type")
        if et and et not in seen:
            seen.add(et)
            out.append(et)
    return out
