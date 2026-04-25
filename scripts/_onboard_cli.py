"""Shared helpers for Onboard troubleshooting CLI scripts."""

from __future__ import annotations

from pathlib import Path


def fallback_api_key_from_stack_env() -> str:
    """Read OFDD_ONBOARD_API_KEY from stack/.env when available."""
    env_path = Path(__file__).resolve().parents[1] / "stack" / ".env"
    if not env_path.exists():
        return ""
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.startswith("OFDD_ONBOARD_API_KEY="):
            continue
        return raw_line.split("=", 1)[1].strip().strip("'").strip('"')
    return ""
