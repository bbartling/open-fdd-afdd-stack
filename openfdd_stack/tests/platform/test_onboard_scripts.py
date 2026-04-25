import subprocess
import sys
import os
from pathlib import Path


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Could not locate repository root")


def test_onboard_list_metadata_requires_api_key():
    script = _repo_root() / "scripts" / "onboard_list_metadata.py"
    env = os.environ.copy()
    env.pop("OFDD_ONBOARD_API_KEY", None)
    proc = subprocess.run(
        [sys.executable, str(script), "--no-stack-env-fallback"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )  # noqa: S603
    assert proc.returncode == 1
    assert "Missing API key" in proc.stderr


def test_onboard_backfill_smoke_requires_api_key():
    script = _repo_root() / "scripts" / "onboard_backfill_smoke.py"
    env = os.environ.copy()
    env.pop("OFDD_ONBOARD_API_KEY", None)
    proc = subprocess.run(
        [sys.executable, str(script), "--no-stack-env-fallback"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )  # noqa: S603
    assert proc.returncode == 1
    assert "Missing API key" in proc.stderr
