"""Typed BACnet error taxonomy.

Callers (API handlers, the future scraper) classify failures so the UX
can give the user something actionable — "device unreachable" is a
different problem from "decode failed on this property" from the user's
perspective even if both surface as a failed read.

Maps onto ``rusty_bacnet.*`` exceptions (``BacnetTimeoutError``,
``BacnetProtocolError``, ``BacnetRejectError``, ``BacnetAbortError``) so
the BipTransport can catch the rusty-bacnet exception, re-raise as our
richer type, and keep user-facing surfaces (API error bodies, log
messages) decoupled from the low-level library.
"""

from __future__ import annotations


class BacnetError(Exception):
    """Base class for every failure originating in the BACnet driver."""


class BacnetDriverError(BacnetError):
    """A driver/plumbing failure that isn't a BACnet protocol error.

    Examples: invalid configuration, attempt to use the driver before
    connecting, graph-write rejection from SeleneDB. Use this (not the
    protocol-level subclasses) for failures on *our* side of the wire.
    """


class BacnetTimeoutError(BacnetError):
    """A BACnet request timed out waiting for a response.

    The device may be offline, on a different network, or the APDU
    timeout is too short. This is almost always a network-layer issue;
    retries usually help.
    """


class BacnetUnreachableError(BacnetError):
    """A device could not be contacted at all (no route, bad address).

    Distinct from :class:`BacnetTimeoutError` because the failure is
    local (e.g. DNS, routing, interface binding) — retrying the exact
    same request will fail the same way.
    """


class BacnetProtocolError(BacnetError):
    """The remote sent a BACnet-level Error PDU (error_class + error_code).

    Common when a device rejects a property read because it doesn't
    expose that property. ``error_class`` and ``error_code`` are the
    raw ASHRAE 135 Clause 18 values.
    """

    def __init__(
        self,
        message: str,
        *,
        error_class: int | None = None,
        error_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.error_class = error_class
        self.error_code = error_code


class BacnetRejectedError(BacnetError):
    """Remote rejected the request (Reject PDU, ASHRAE 135 Clause 18.8).

    ``reason`` is the raw reject-reason code (0 = OTHER, 1 =
    BUFFER_OVERFLOW, 9 = UNRECOGNIZED_SERVICE, …).
    """

    def __init__(self, message: str, *, reason: int | None = None) -> None:
        super().__init__(message)
        self.reason = reason


class BacnetAbortedError(BacnetError):
    """Transaction was aborted by the remote (Abort PDU, Clause 18.9).

    ``reason`` is the raw abort-reason code (0 = OTHER, 4 = SEGMENTATION_NOT_SUPPORTED, …).
    """

    def __init__(self, message: str, *, reason: int | None = None) -> None:
        super().__init__(message)
        self.reason = reason


class BacnetDecodeError(BacnetError):
    """A property value came back but couldn't be decoded into a Python type.

    Raised when rusty-bacnet hands us a ``PropertyValue`` whose tag we
    don't know how to translate (e.g. vendor-specific constructed type).
    The raw value is preserved in ``raw`` so the caller can inspect it.
    """

    def __init__(self, message: str, *, raw: object | None = None) -> None:
        super().__init__(message)
        self.raw = raw
