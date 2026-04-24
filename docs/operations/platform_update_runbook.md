---
title: Platform update runbook
parent: Operations
nav_order: 30
---

# Platform update runbook

Use this runbook for repeatable Open-FDD upgrades when new patches are released.

## Recommended default (most sites)

```bash
cd open-fdd-afdd-stack
./scripts/bootstrap.sh --maintenance --update --verify
```

What this does:
- Pulls latest commits for this repo and sibling `diy-bacnet-server` (when present).
- Rebuilds/restarts containers when commits changed (otherwise restart only).
- Keeps Timescale/Postgres data (sites, equipment, points, data model, timeseries).
- Runs HTTP/BACnet health checks via `--verify`.

## Safer patch cycle (higher-risk changes)

```bash
cd open-fdd-afdd-stack
./scripts/bootstrap.sh --maintenance --update --verify --force-rebuild --test --diy-bacnet-tests
```

Use this when dependencies changed, CI recently failed, or you want stronger local evidence before handing the system back to operators.

## Backup-first workflow (recommended for production-like systems)

1. Export data model JSON (`GET /data-model/export`) and save with date/time.
2. Optionally save TTL (`GET /data-model/ttl?save=true`) for semantic diff.
3. Run one of the update commands above.
4. Validate post-update:
   - API `/health`
   - BACnet `/bacnet/server_hello`
   - Data Model Testing SPARQL summaries (AHU/VAV/class summary).

If something breaks in model semantics, use your saved JSON to restore via `PUT /data-model/import`.

## Important flags during upgrades

- `--purge-timeseries`: clears timeseries only, keeps model.
- `--reset-data`: destructive test-bench reset (deletes all sites/model data + timeseries).
- `--enforce-network-default`: rewrites persisted graph config to canonical defaults (`bacnet_server_url=http://caddy:8081`, scrape interval 5 min, etc.).

Do not use `--reset-data` for normal upgrades.

## AI-assisted modeling guardrail

For ChatGPT/LLM-assisted tagging, require import payloads to return JSON with only:

```json
{
  "points": [],
  "equipment": []
}
```

No extra top-level keys (`sites`, `relationships`, `equipments`, etc.). Unknown nested keys are rejected too. Validate locally first:

```bash
python scripts/validate_data_model_import.py path/to/import.json
```
