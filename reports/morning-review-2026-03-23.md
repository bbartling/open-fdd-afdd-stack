# Morning Review — 2026-03-23

- **Review time:** 2026-03-23 06:10 CDT
- **Source logs checked:**
  - `C:\Users\ben\OneDrive\Desktop\testing\automated_testing\overnight_bacnet.log`
  - `C:\Users\ben\OneDrive\Desktop\testing\automated_testing\automated_suite.log`
- **Reviewer:** OpenClaw

## Executive summary

The overnight run did **not** produce evidence of a fresh confirmed Open-FDD product regression strong enough to justify a new GitHub issue this morning.

What the logs do show is:
- **Selenium/frontend smoke passed**
- **SPARQL/API parity failed** because direct backend requests hit **401 Missing or invalid Authorization header**
- **`automated_suite.log` is missing**
- **Long-run BACnet/FDD verification and hot-reload verification were not reached** because the orchestrator stops on first failing step
- BACnet discovery for device `3456790` showed **mixed behavior** in `overnight_bacnet.log`: one pass hit HTTP 422, another later pass succeeded

## Suite-by-suite status

### 1. Selenium / frontend suite
**Status:** PASS

Evidence from `overnight_bacnet.log`:
- site creation and import succeeded
- malformed/missing-site negative imports were rejected as expected
- data model page checks passed
- points page unit checks passed
- points device tree rendered expected columns
- context-menu polling toggle worked on `SA-T`
- plots page loaded and showed a fault in the legend
- overview page loaded
- weather page was resilient (still asked to select a site)
- explicit log line: `=== E2E frontend tests passed ===`

### 2. SPARQL parity / backend direct API checks
**Status:** FAIL

Observed failures:
- `POST /data-model/sparql/upload` → `401 Missing or invalid Authorization header`
- `GET /sites` → `401 Missing or invalid Authorization header`
- `POST /data-model/sparql` for the per-query loop → repeated `401 Missing or invalid Authorization header`
- parity re-fetches for predefined queries also failed for the same reason
- log ends with:
  - `28 query/queries failed.`
  - `SPARQL CRUD + frontend parity failed with exit code 1`

### 3. BACnet scraping / BACnet discovery
**Status:** MIXED / INCONCLUSIVE

Observed:
- In one pass, device `3456789` was added successfully while device `3456790` failed `POST /bacnet/point_discovery_to_graph` with **422 Unprocessable Entity**.
- In a later pass in the same overnight log, **both** `3456789` and `3456790` were added successfully.

Interpretation:
- This is **not** a clean all-night pass.
- It is also **not** a cleanly reproducible product failure from the evidence currently available.
- The 3456790 behavior looks intermittent or state-dependent and needs re-checking before opening a product bug.

### 4. FDD verification
**Status:** NOT VERIFIED

Reason:
- No durable evidence in the checked logs confirms that long-run BACnet scrape + fault-schedule verification completed.
- Because the orchestrator aborts on the first failing step, the SPARQL parity failure likely prevented the long-run FDD step from running.

### 5. Hot-reload verification
**Status:** NOT VERIFIED

Reason:
- Same orchestration issue as above.
- No evidence in the checked logs that the hot-reload step ran to completion.

## Log availability / orchestration notes

### `automated_suite.log`
**Status:** missing

Observed result:
- `MISSING_AUTOMATED_SUITE_LOG`

Interpretation:
- Either the expected wrapper log was never created, or the run path still only appended to `overnight_bacnet.log`.
- This is a tooling/reporting gap and makes morning triage noisier than it should be.

### Orchestrator behavior
The orchestrator script (`automated_suite.py`) raises `SystemExit` on the first non-zero step.

Given the observed line:
- `SPARQL CRUD + frontend parity failed with exit code 1`

it is highly likely that:
- long-run BACnet scrape/fault validation did **not** run
- hot-reload validation did **not** run

## Classification

### Auth/config drift
- direct backend SPARQL/API checks failed with `401 Missing or invalid Authorization header`
- this still looks like bench-side auth/config drift rather than a confirmed Open-FDD backend bug

### Testbench / tooling limitations
- `automated_suite.log` missing
- first-failure orchestration prevents later overnight steps from running, which weakens the morning evidence chain

### Possible product rough edge (not yet confirmed)
- intermittent `3456790` BACnet discovery 422 in one pass, followed by later success in another pass
- not strong enough yet for a clean product issue without reproduction and better backend/container evidence

## GitHub issue decision

### `bbartling/open-fdd`
**No new issue posted this morning.**

Reason:
- No newly confirmed Open-FDD bug was isolated strongly enough from environment/auth drift.
- The docs broken-link issue already exists as:
  - `bbartling/open-fdd#82` — **Broken README links for LLM workflow docs and canonical prompt file**

### `bbartling/open-fdd-automated-testing`
The bench/auth/tooling gap already has a tracking issue:
- `bbartling/open-fdd-automated-testing#1` — **Track remaining overnight BACnet verification and SPARQL auth gaps**

## Recommended next actions

1. **Fix bench auth first** so unattended direct `POST /data-model/sparql` checks can run.
2. **Make the orchestrator continue-on-failure or always emit a summary log**, so long-run BACnet/FDD and hot-reload evidence are still captured even if SPARQL parity fails.
3. **Re-run BACnet discovery for device `3456790` with backend/container logs available** before filing any product bug.
4. **Ensure `automated_suite.log` is actually created**, since the morning review explicitly expects it.

## Bottom line

- **Selenium / frontend:** passed
- **SPARQL parity:** failed due to `401` auth/header problem
- **BACnet scraping/discovery:** mixed / inconclusive
- **FDD verification:** not confirmed
- **Hot-reload verification:** not confirmed
- **New GitHub bug issue this morning:** no
