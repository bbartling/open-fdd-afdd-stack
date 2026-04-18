"""BACnet ObjectType → Mnemosyne CURIE mapping."""

from __future__ import annotations

import pytest

from openfdd_stack.platform.bacnet import (
    OBJECT_TYPE_TO_CURIE,
    curie_for_object_type,
)
from openfdd_stack.platform.bacnet.object_types import BACNET_OBJECT_ROOT_CURIE


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (0, "mnemo:BacnetAnalogInput"),
        (1, "mnemo:BacnetAnalogOutput"),
        (2, "mnemo:BacnetAnalogValue"),
        (3, "mnemo:BacnetBinaryInput"),
        (8, "mnemo:BacnetDevice"),
        (13, "mnemo:BacnetMultiStateInput"),
        (19, "mnemo:BacnetMultiStateValue"),
        (28, "mnemo:BacnetLoadControl"),
        (64, "mnemo:BacnetColorTemperature"),
    ],
)
def test_standard_types_map_to_mnemosyne_concept(raw, expected):
    """Every ASHRAE 135 Clause 12 object-type has a named Mnemosyne concept."""
    assert curie_for_object_type(raw) == expected


def test_proprietary_type_falls_through_to_root():
    """Vendor-proprietary object types anchor at the root concept."""
    assert curie_for_object_type(500) == BACNET_OBJECT_ROOT_CURIE
    assert curie_for_object_type(1022) == BACNET_OBJECT_ROOT_CURIE


def test_mapping_covers_standard_range_0_to_64():
    """Every standard object-type (0–64) must be present — no gaps."""
    for raw in range(0, 65):
        assert raw in OBJECT_TYPE_TO_CURIE, f"gap at object-type {raw}"


def test_all_curies_follow_mnemo_bacnet_prefix():
    """Schema/pack expectation: CURIEs live under the ``mnemo:Bacnet`` namespace."""
    for curie in OBJECT_TYPE_TO_CURIE.values():
        assert curie.startswith("mnemo:Bacnet"), curie
