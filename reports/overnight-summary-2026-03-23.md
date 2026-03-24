# Overnight Summary — 2026-03-23

- **Snapshot time:** 2026-03-23 23:15 CDT
- **Window:** Open-FDD dev-testing window (18:00–06:00 CDT)
- **Branch context:** `master` for published docs review; active PR under watch: `develop/v2.0.7` -> `master` (PR #83)
- **Reviewer:** OpenClaw

## 1. Executive summary

The overnight state improved meaningfully versus the earlier auth-drift-heavy picture, but the full evidence chain is still not completely closed.

High-signal findings from this overnight window:

1. **Direct authenticated backend SPARQL is working from this host now.** The daytime auth-path fix appears to be holding.
2. **DIY BACnet gateway live reads are working** once the correct JSON-RPC request envelope is used.
3. **Docker/container evidence is still unavailable from this host** because Docker Desktop Linux engine access remains missing.
4. **Published docs route fragility still exists** for `llm_workflow`: the trailing-slash URL still 404s while the no-trailing-slash route works.
5. **The active PR context changed** from older notes: the current live PR under review is now **#83 `develop/v2.0.7` -> `master`**.
6. **End-to-end fault-calculation proof is still not fully closed** tonight even though BACnet-side independent reads and backend SPARQL are now both working.

## 2. Active PR review

### PR #83 — `develop/v2.0.7` -> `master`
- URL: <https://github.com/bbartling/open-fdd/pull/83>
- Status at review time: open, not draft
- Last update: 2026-03-23 14:13Z
- CI status at review time:
  - `test` workflow: **SUCCESS**
  - `CodeRabbit`: **SUCCESS**

### Review assessment
- **Overall state:** PR appears healthy from a CI/review-status perspective.
- This PR is now the correct active dev-branch context for any overnight docs/link review beyond `master`.

### Classification
- **active branch/review context update**, not a defect by itself

## 3. Docs and README link verification

### Checked against published `master` docs
- <https://bbartling.github.io/open-fdd/> -> 200
- <https://bbartling.github.io/open-fdd/modeling/llm_workflow/> -> 404
- <https://bbartling.github.io/open-fdd/modeling/llm_workflow> -> 200
- <https://github.com/bbartling/open-fdd/blob/master/pdf/open-fdd-docs.pdf> -> 200

### Interpretation
- The **published docs route remains fragile/inconsistent** for `llm_workflow`.
- Humans and agents following the trailing-slash route still hit a broken page.

### Classification
- **documentation gap / route inconsistency**

## 4. Container-log / runtime evidence

### Docker access from this host
Attempted:
- `docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"`

Observed:
- Docker Desktop Linux engine pipe unavailable:
  - `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`

### Interpretation
- Live container review for `api`, `frontend`, `bacnet-scraper`, `fdd-loop`, `host-stats`, and `bacnet-server` is still blocked from this host.
- This remains a major limitation on proving backend/runtime causality from this workstation alone.

### Classification
- **testbench limitation**

## 5. Backend auth / graph evidence

### Direct backend checks
Authenticated direct backend SPARQL returned **200** during this window.

Examples observed:
- site query returned one site binding:
  - `http://openfdd.local/site#site_c6fd9156_7591_4840_ad23_15e78588dfe5`
- site count query returned:
  - `1`
- point count query returned:
  - `13`

### Interpretation
- The earlier blanket `401 Missing or invalid Authorization header` state is no longer the dominant story for this host.
- Backend auth/config from the active launch context appears materially improved.

### Classification
- **improved auth/config state**

## 6. BACnet / graph / live read verification

### Gateway contract finding
The DIY BACnet gateway at `:8080` is a **JSON-RPC API**, not a plain REST body-per-method API.

A naive body failed earlier with JSON-RPC validation errors.

The corrected `client_read_property` shape is:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "client_read_property",
  "params": {
    "request": {
      "device_instance": 3456790,
      "object_identifier": "analog-value,1",
      "property_identifier": "present-value"
    }
  }
}
```

### Confirmed live BACnet-side reads
Using the corrected JSON-RPC envelope, live reads succeeded for representative points on device `3456790`:

- `analog-value,1` `present-value` -> **72.0**
- `analog-input,2` `present-value` -> **378.2156677246094**
- `analog-value,3` `present-value` -> **800.0**

### Interpretation
- the DIY BACnet gateway is reachable
- BACnet-side independent reads are working
- the earlier malformed call should be treated as a tooling/API-contract mistake, not a BACnet outage

### Classification
- **BACnet-side read path confirmed working**
- **tooling / API-contract mismatch corrected**

## 7. Fault-calculation / FDD status

### What is now stronger than before
Tonight's evidence is better than the earlier morning picture because:
- backend SPARQL auth is working
- independent BACnet-side reads are working

### What is still missing
The full end-to-end proof chain is still not fully closed:
1. fake BACnet device produces the expected fault-window behavior
2. telemetry is ingested into Open-FDD
3. model/SPARQL context matches the relevant devices/points
4. YAML rules + rolling-window conditions are satisfied
5. fault outputs are visible in Open-FDD APIs/UI exactly when expected

### Verdict for this window
- **FDD/fault-verification status:** **INCONCLUSIVE**

### Why inconclusive
Because although the BACnet-side and backend-SPARQL sides are both alive, this pass still lacks a complete correlated proof of fault outputs over the expected fake-device schedule/rolling-window horizon.

### Classification
- **evidence gap / incomplete overnight proof chain**

## 8. Roll-up classification

- **Improved auth/config state**
  - direct authenticated backend SPARQL now works from this host
- **Documentation gap**
  - trailing-slash `llm_workflow/` route still 404s
- **Testbench limitation**
  - Docker/container evidence still unavailable from this host
- **Corrected tooling issue**
  - DIY BACnet gateway requires JSON-RPC request envelopes; malformed body was the earlier cause of failure
- **Remaining evidence gap**
  - end-to-end fault-calculation proof still not fully established tonight

## 9. Highest-value next steps

1. correlate the successful BACnet-side reads with modeled points and Open-FDD fault outputs across the fake-device schedule
2. explicitly validate `/faults/active`, `/faults/state`, or downloadable fault outputs against rolling-window expectations
3. continue isolating any remaining SPARQL/frontend parity rough edges after the auth improvement
4. restore Docker/runtime access on the bench host if container-causality evidence is required

## 10. Current overnight verdict

### Trust level
**Better than morning, but still cautious.**

### Why
- backend auth is materially improved
- independent BACnet-side reads are materially improved
- but full fault-calculation proof is still not closed end-to-end

That makes tonight useful and materially better than the earlier auth-drift state, but not yet a perfect all-clear certification run.
