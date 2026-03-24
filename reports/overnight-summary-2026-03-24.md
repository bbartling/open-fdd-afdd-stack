# Open-FDD overnight summary — 2026-03-24 04:00 CDT

## Scope
- Overnight review window pass during the active 6 PM–6 AM workflow.
- Focused on current PR state, docs/link health, backend auth + graph integrity, model-derived BACnet addressing, and BACnet RPC spot-checks.
- Normal 10-minute integrity sweep intentionally stood down because the dedicated overnight workflow was already active.

## Environment mode
- **Mode:** TEST BENCH
- **Mode basis:** fake BACnet devices `3456789` and `3456790`, known bench frontend/backend/BACnet routes on `192.168.204.16`, synthetic point names and values, and overnight-testing repo workflows tailored to the bench.
- **Operator alert level:** INFO with a few actionable warnings
- **Seasonal/time basis:** 04:00 CDT, late-night overnight dev-testing window; bench state matters more than real HVAC comfort logic here.

## Executive summary
- Direct backend auth is working again from the current bench context.
- Open-FDD graph integrity is reachable and non-empty.
- Model-derived BACnet addressing is present for both expected fake devices.
- DIY BACnet server RPC reads are working and broadly align with the graph-derived addressing.
- Docker/container log review is still blocked from this host because Docker Desktop’s Linux engine pipe is unavailable.
- The main docs/link issue on `master` remains the broken trailing-slash LLM workflow link.
- Current open PR `bbartling/open-fdd#83` looks low risk: it is a version-bump/release-prep PR with green CI and no obvious code-path regression in the diff.

## PR review
### `bbartling/open-fdd#83` — `Develop/v2.0.7`
- **Base/head:** `develop/v2.0.7` -> `master`
- **Scope:** version bumps only in `pyproject.toml`, `frontend/package.json`, and `frontend/package-lock.json`
- **CI:** green (`CI / test` success)
- **CodeRabbit:** success
- **Review stance:** near-zero functional risk from the diff itself

### PR notes
- This PR targeting `master` is reasonable as a release-prep move.
- Repo docs/README still broadly tell contributors to target `develop`; that is fine for normal feature work, but the docs could be clearer that release/version-bump PRs are an expected exception.

## Backend and graph checks
### PASS — authenticated backend access
- Authenticated `GET /data-model/check` succeeded.
- Authenticated `POST /data-model/sparql` succeeded from the current bench context.

### PASS — graph/data-model integrity reachable
Observed from `/data-model/check`:
- `sites=1`
- `bacnet_devices=2`
- `triple_count=80003`
- warning present for **20108 orphan blank nodes**

Interpretation:
- The graph is alive and populated.
- The orphan blank-node warning is not new enough by itself to call a fresh product bug, but it remains worth watching because it can pollute count-oriented checks and operator trust.

### PASS — SPARQL evidence
Using repo SPARQL assets against the live backend:
- `04_bacnet_devices.sparql` returned both expected devices: `bacnet://3456789`, `bacnet://3456790`
- `06_polling_points_brick_type.sparql` returned **37** polling/model rows
- `08_bacnet_telemetry_points.sparql` returned **37** rows total, with **23** rows carrying BACnet device/object addressing
- `07_count_triples.sparql` returned **84629** in the current query path
- `24_operator_site_context.sparql` returned site label `TestBenchSite`

## Important tooling lesson
### Documentation gap / tooling drift
The current backend `/data-model/sparql` response shape in this bench is:

```json
{"bindings": [...]} 
```

not strict SPARQL JSON:

```json
{"results": {"bindings": [...]}}
```

This matters because early bench checks that only parsed `results.bindings` falsely looked empty even though the graph was healthy. That is **tooling/API-contract drift**, not proof that the graph was empty.

I updated testing-repo docs to preserve this for future clones.

## BACnet model vs live RPC comparison
### PASS — gateway reachability
- `http://192.168.204.16:8080/openapi.json` reachable
- JSON-RPC endpoints visible, including `client_read_property`, `server_hello`, and `server_read_all_values`
- `server_hello` succeeded and reported MQTT bridge connected

### PASS — model-derived addressing present
Representative graph-derived BACnet rows:
- `DAP-P` -> device `3456789`, address `192.168.204.13`, object `analog-input,1`
- `SA-T` -> device `3456789`, address `192.168.204.13`, object `analog-input,2`
- `MA-T` -> device `3456789`, address `192.168.204.13`, object `analog-input,3`
- `RA-T` -> device `3456789`, address `192.168.204.13`, object `analog-input,4`
- `OA-T` -> device `3456789`, address `192.168.204.13`, object `analog-input,6`
- `HTG-O` -> device `3456789`, address `192.168.204.13`, object `analog-output,2`
- `CLG-O` -> device `3456789`, address `192.168.204.13`, object `analog-output,3`
- `DPR-O` -> device `3456789`, address `192.168.204.13`, object `analog-output,4`
- `ZoneTemp` -> device `3456790`, address `192.168.204.14`, object `analog-input,1`
- `VAVDamperCmd` -> device `3456790`, address `192.168.204.14`, object `analog-output,1`
- `ZoneCoolingSpt` -> device `3456790`, address `192.168.204.14`, object `analog-value,1`

### PASS — live BACnet RPC spot reads
Representative JSON-RPC `client_read_property` results:
- `DAP-P` (`3456789`, `analog-input,1`) = `1.4722`
- `SA-T` (`3456789`, `analog-input,2`) = `70.4765`
- `MA-T` (`3456789`, `analog-input,3`) = `74.5650`
- `RA-T` (`3456789`, `analog-input,4`) = `66.3011`
- `OA-T` (`3456789`, `analog-input,6`) = `35.2552`
- `SF-O` (`3456789`, `analog-output,1`) = `50.0`
- `HTG-O` (`3456789`, `analog-output,2`) = `0.0`
- `CLG-O` (`3456789`, `analog-output,3`) = `0.0`
- `DPR-O` (`3456789`, `analog-output,4`) = `0.0`
- `DAP-SP` (`3456789`, `analog-value,1`) = `1.0`
- `SAT-SP` (`3456789`, `analog-value,2`) = `55.0`
- `ZoneTemp` (`3456790`, `analog-input,1`) = `72.7614`
- `VAVFlow` (`3456790`, `analog-input,2`) = `361.0730`
- `VAVDamperCmd` (`3456790`, `analog-output,1`) = `50.0`
- `ZoneCoolingSpt` (`3456790`, `analog-value,1`) = `72.0`
- `ZoneDemand` (`3456790`, `analog-value,2`) = `56.4580`
- `VAVFlowSpt` (`3456790`, `analog-value,3`) = `800.0`

## HVAC / FDD sanity interpretation
Because this is a **test bench**, the goal is not real-building comfort judgment; it is whether the values are readable and mechanically plausible enough for the fake device model.

### Broad sanity summary
- AHU-ish fake points are readable and internally plausible.
- VAV-ish fake points are readable and internally plausible.
- The graph-derived BACnet addressing matches live BACnet RPC reads for sampled points.

### Relation to current YAML fault rules
Single-snapshot judgment only:
- `duct_static_low_at_full_speed` / `low_duct_static_at_max_fan`: **not suggested** by the sampled snapshot, because `DAP-P` is above `DAP-SP` and fan command was only `50%`, not near max.
- Cooling/heating SAT-vs-MAT rules are **not strongly suggested** by this snapshot because both heating and cooling valve commands were `0%`, so the active-mode preconditions are not met.
- The snapshot is **not enough** to judge rolling-window rules like hunting/flatline behavior.

### Rolling-window expectation note
Rules with parameters like `window: 60`, `window: 12`, or `rolling_window: 6` cannot be meaningfully confirmed from a single BACnet spot read. Those remain overnight/trend-path validations, not instant point-read validations.

## Frontend / parity / prior overnight evidence
Using the latest overnight log already on disk:
- frontend Selenium passed earlier in the run
- BACnet discovery for both fake devices succeeded earlier in the run
- SPARQL frontend/API parity still showed several mismatches on count-style queries, especially triple-count and orphan-reference style checks

Interpretation:
- There is still a likely **product bug or timing/synchronization weakness** in frontend-vs-backend SPARQL parity for count-sensitive queries under a changing graph.
- The evidence is stronger for parity instability than for total backend failure.

## Docs / link review
### PASS
- Docs home: `https://bbartling.github.io/open-fdd/` loads
- LLM workflow page without trailing slash: `https://bbartling.github.io/open-fdd/modeling/llm_workflow` loads

### FAIL — documentation link on `master`
- `https://bbartling.github.io/open-fdd/modeling/llm_workflow/` returns **404**
- `open-fdd/README.md` still links to the **trailing-slash** form

Classification:
- **documentation gap** / broken link on `master`

### Additional docs gap
- Contributor guidance says PRs should target `develop`, but current release/version-bump PRs are targeting `master`.
- This is not necessarily wrong, but docs should explain the release exception more explicitly for humans and AI agents.

## Container/log observability
### INCONCLUSIVE — host-side Docker/container log review blocked
Attempted `docker ps` from this host failed with missing Docker Desktop Linux engine pipe:
- `//./pipe/dockerDesktopLinuxEngine` unavailable

Classification:
- **testbench limitation**

Impact:
- Could not directly inspect container logs for `api`, `frontend`, `bacnet-scraper`, `fdd-loop`, `host-stats`, or `bacnet-server` from this machine during this pass.

## Classification summary
### Product bugs / likely product behavior
- Frontend-vs-backend SPARQL parity remains unstable on count-oriented queries under current graph conditions.

### Setup drift / auth/config drift
- Auth drift is **not active right now**; backend auth is presently healthy.
- However, auth remains launcher-context-sensitive and can still regress if the actual overnight environment loses `OFDD_API_KEY`.

### Documentation gaps
- Broken trailing-slash LLM workflow link in `open-fdd/README.md`
- Contributor docs should better explain the `develop` default vs `master` release exception
- Testing repo needed a note about `/data-model/sparql` response shape tolerance

### Testbench limitations
- Docker/container logs blocked from this host
- Single-snapshot BACnet reads cannot prove rolling-window fault results

## Repo notes updated tonight
Sanitized durable context added to the automated-testing repo docs:
- auth restored on current bench context
- `/data-model/sparql` response shape can be `{"bindings": [...]}`
- test tooling should tolerate both `bindings` and `results.bindings`

## Recommended next actions
1. Fix the README LLM workflow link on `open-fdd/master` to use the working no-trailing-slash URL.
2. Clarify contributor/release docs so normal feature PRs target `develop`, while release/version-bump PRs targeting `master` are explicitly documented.
3. Make bench scripts tolerant to both SPARQL response shapes everywhere, not just in ad hoc troubleshooting.
4. When host access allows, restore container-log observability for the overnight workflow so parity failures can be correlated with live service logs.
5. Keep treating count-sensitive frontend/API parity mismatches as higher-value bug evidence than generic auth suspicion, because auth is currently working.
