"""Driver profile loader for config/drivers.yaml."""

from __future__ import annotations

import os
import re
from pathlib import Path

DEFAULT_DRIVER_PROFILE: dict[str, bool] = {
    "bacnet": True,
    "fdd": True,
    "weather": True,
    "onboard": False,
    "csv": False,
    "host_stats": True,
}


def _parse_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return None


def _default_profile_path() -> Path:
    env_path = (os.getenv("OFDD_DRIVER_PROFILE_FILE") or "").strip()
    if env_path:
        p = Path(env_path)
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    return (Path(__file__).resolve().parents[2] / "config" / "drivers.yaml").resolve()


def load_driver_profile() -> tuple[dict[str, bool], Path, bool]:
    """Return (drivers, path, exists) from drivers.yaml with safe fallbacks."""
    path = _default_profile_path()
    drivers = dict(DEFAULT_DRIVER_PROFILE)
    if not path.exists():
        return drivers, path, False

    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
        doc_drivers = data.get("drivers", {}) if isinstance(data, dict) else {}
        if isinstance(doc_drivers, dict):
            for key in DEFAULT_DRIVER_PROFILE:
                parsed = _parse_bool(doc_drivers.get(key))
                if parsed is not None:
                    drivers[key] = parsed
        return drivers, path, True
    except Exception:
        pass

    # Lightweight fallback parser for simple key: bool values under drivers:
    in_drivers = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^\s*drivers\s*:\s*$", line):
            in_drivers = True
            continue
        if in_drivers and re.match(r"^\S", line):
            in_drivers = False
        if not in_drivers:
            continue
        for key in DEFAULT_DRIVER_PROFILE:
            m = re.match(r"^\s*" + re.escape(key) + r"\s*:\s*(.*?)\s*$", line)
            if not m:
                continue
            token = m.group(1).split("#", 1)[0].strip().strip('"').strip("'")
            parsed = _parse_bool(token)
            if parsed is not None:
                drivers[key] = parsed
            break
    return drivers, path, True
