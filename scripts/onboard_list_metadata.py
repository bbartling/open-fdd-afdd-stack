#!/usr/bin/env python3
"""List Onboard buildings and point metadata for troubleshooting."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from openfdd_stack.platform.drivers.onboard import OnboardClient, parse_building_filters


def _fallback_api_key_from_stack_env() -> str:
    env_path = Path(__file__).resolve().parents[1] / "stack" / ".env"
    if not env_path.exists():
        return ""
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.startswith("OFDD_ONBOARD_API_KEY="):
            continue
        val = raw_line.split("=", 1)[1].strip().strip("'").strip('"')
        return val
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="List Onboard metadata")
    parser.add_argument(
        "--api-base-url",
        default=os.getenv("OFDD_ONBOARD_API_BASE_URL", "https://api.onboarddata.io"),
    )
    parser.add_argument("--api-key", default=os.getenv("OFDD_ONBOARD_API_KEY", ""))
    parser.add_argument(
        "--building-ids",
        default=os.getenv("OFDD_ONBOARD_BUILDING_IDS", ""),
        help="CSV or JSON array (ex: 66,67 or [66,67])",
    )
    parser.add_argument(
        "--building",
        action="append",
        default=[],
        help='Building name filter (repeatable), e.g. --building "Office Building"',
    )
    parser.add_argument(
        "--no-stack-env-fallback",
        action="store_true",
        help="Do not read OFDD_ONBOARD_API_KEY from stack/.env when --api-key is empty",
    )
    args = parser.parse_args()

    api_key = (args.api_key or "").strip()
    if not api_key and not args.no_stack_env_fallback:
        api_key = _fallback_api_key_from_stack_env()
    if not api_key:
        print("Missing API key. Set --api-key or OFDD_ONBOARD_API_KEY.", file=sys.stderr)
        return 1

    client = OnboardClient(base_url=args.api_base_url, api_key=api_key)
    filters = parse_building_filters(args.building_ids)
    filters.extend([b for b in args.building if str(b).strip()])
    buildings = client.get_buildings(filters)

    out: list[dict] = []
    for b in buildings:
        bldg_id = int(b["id"])
        points = client.get_points(bldg_id)
        out.append(
            {
                "building_id": bldg_id,
                "name": b.get("name"),
                "point_count": len(points),
                "sample_points": points[:5],
            }
        )
    print(json.dumps({"buildings": out}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
