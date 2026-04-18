"""BACnet ObjectType → Mnemosyne CURIE mapping.

The ``bacnet_object`` schema pack type (``config/schema_packs/bacnet-driver.json``)
carries a ``concept_curie: string!`` field linking each discovered object to a
Mnemosyne concept (``mnemo:BacnetAnalogInput`` for object-type 0, etc.).
Mnemosyne in turn carries ``equivalentTo`` edges into Brick / 223P /
Haystack, so downstream queries like "all analog inputs in this AHU"
work against the canonical vocabulary instead of BACnet-specific strings.

Mapping is built from ASHRAE 135-2020 Clause 12 (object types 0–64).
Vendor-proprietary types (128–1023) fall through :func:`curie_for_object_type`
to ``mnemo:BacnetObject`` — the root concept — so the graph still gets a
node that participates in "is a BACnet object" queries.
"""

from __future__ import annotations

# Keyed by the raw BACnet object-type integer (Clause 12), which
# matches rusty-bacnet's ``ObjectType.to_raw()`` return value.
# Values are the canonical Mnemosyne CURIEs from
# ``selenepack-smartbuildings/curated/protocols/bacnet_objects.json``.
OBJECT_TYPE_TO_CURIE: dict[int, str] = {
    0: "mnemo:BacnetAnalogInput",
    1: "mnemo:BacnetAnalogOutput",
    2: "mnemo:BacnetAnalogValue",
    3: "mnemo:BacnetBinaryInput",
    4: "mnemo:BacnetBinaryOutput",
    5: "mnemo:BacnetBinaryValue",
    6: "mnemo:BacnetCalendar",
    7: "mnemo:BacnetCommand",
    8: "mnemo:BacnetDevice",
    9: "mnemo:BacnetEventEnrollment",
    10: "mnemo:BacnetFile",
    11: "mnemo:BacnetGroup",
    12: "mnemo:BacnetLoop",
    13: "mnemo:BacnetMultiStateInput",
    14: "mnemo:BacnetMultiStateOutput",
    15: "mnemo:BacnetNotificationClass",
    16: "mnemo:BacnetProgram",
    17: "mnemo:BacnetSchedule",
    18: "mnemo:BacnetAveraging",
    19: "mnemo:BacnetMultiStateValue",
    20: "mnemo:BacnetTrendLog",
    21: "mnemo:BacnetLifeSafetyPoint",
    22: "mnemo:BacnetLifeSafetyZone",
    23: "mnemo:BacnetAccumulator",
    24: "mnemo:BacnetPulseConverter",
    25: "mnemo:BacnetEventLog",
    26: "mnemo:BacnetGlobalGroup",
    27: "mnemo:BacnetTrendLogMultiple",
    28: "mnemo:BacnetLoadControl",
    29: "mnemo:BacnetStructuredView",
    30: "mnemo:BacnetAccessDoor",
    31: "mnemo:BacnetTimer",
    32: "mnemo:BacnetAccessCredential",
    33: "mnemo:BacnetAccessPoint",
    34: "mnemo:BacnetAccessRights",
    35: "mnemo:BacnetAccessUser",
    36: "mnemo:BacnetAccessZone",
    37: "mnemo:BacnetCredentialDataInput",
    38: "mnemo:BacnetNetworkSecurity",
    39: "mnemo:BacnetBitStringValue",
    40: "mnemo:BacnetCharacterStringValue",
    41: "mnemo:BacnetDatePatternValue",
    42: "mnemo:BacnetDateValue",
    43: "mnemo:BacnetDateTimePatternValue",
    44: "mnemo:BacnetDateTimeValue",
    45: "mnemo:BacnetIntegerValue",
    46: "mnemo:BacnetLargeAnalogValue",
    47: "mnemo:BacnetOctetStringValue",
    48: "mnemo:BacnetPositiveIntegerValue",
    49: "mnemo:BacnetTimePatternValue",
    50: "mnemo:BacnetTimeValue",
    51: "mnemo:BacnetNotificationForwarder",
    52: "mnemo:BacnetAlertEnrollment",
    53: "mnemo:BacnetChannel",
    54: "mnemo:BacnetLightingOutput",
    55: "mnemo:BacnetBinaryLightingOutput",
    56: "mnemo:BacnetNetworkPort",
    57: "mnemo:BacnetElevatorGroup",
    58: "mnemo:BacnetEscalator",
    59: "mnemo:BacnetLift",
    60: "mnemo:BacnetStaging",
    61: "mnemo:BacnetAuditReporter",
    62: "mnemo:BacnetAuditLog",
    63: "mnemo:BacnetColor",
    64: "mnemo:BacnetColorTemperature",
}

# Parent/root concept used as the fallback for vendor-proprietary types.
BACNET_OBJECT_ROOT_CURIE = "mnemo:BacnetObject"


def curie_for_object_type(raw_type: int) -> str:
    """Return the Mnemosyne CURIE for a BACnet object-type integer.

    Standard types (0–64) map to their specific concept. Vendor
    proprietary types (128+) return :data:`BACNET_OBJECT_ROOT_CURIE` so
    the graph still anchors them under the BACnet object hierarchy —
    vendor-specific subclassing can be added later without changing the
    call sites.
    """
    return OBJECT_TYPE_TO_CURIE.get(raw_type, BACNET_OBJECT_ROOT_CURIE)
