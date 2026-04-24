#!/usr/bin/env python3
"""Validate a data-model import JSON payload against DataModelImportBody.

Usage:
  python scripts/validate_data_model_import.py path/to/import.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from openfdd_stack.platform.api.data_model import DataModelImportBody


def _format_loc(loc: tuple[object, ...] | list[object]) -> str:
    parts: list[str] = []
    for segment in loc:
        if segment == "body":
            continue
        if isinstance(segment, int):
            if parts:
                parts[-1] = f"{parts[-1]}[{segment}]"
            else:
                parts.append(f"[{segment}]")
            continue
        parts.append(str(segment))
    return ".".join(parts) if parts else "body"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate JSON payload for PUT /data-model/import."
    )
    parser.add_argument("json_file", type=Path, help="Path to JSON payload file")
    args = parser.parse_args()

    try:
        raw = args.json_file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read file: {exc}", file=sys.stderr)
        return 2

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}")
        return 2

    try:
        parsed = DataModelImportBody.model_validate(payload)
    except ValidationError as exc:
        errors = exc.errors()
        print(f"INVALID: {len(errors)} validation error(s)")
        for idx, err in enumerate(errors, start=1):
            loc = _format_loc(err.get("loc", []))
            msg = err.get("msg", "Validation error")
            err_type = err.get("type", "unknown")
            print(f"{idx}. {loc}: {msg} ({err_type})")
        return 1

    point_count = len(parsed.points)
    equipment_count = len(parsed.equipment)
    print(
        f"VALID: payload accepted ({point_count} point row(s), {equipment_count} equipment row(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
