# Overnight Summary — 2026-03-22

- **Window start:** 2026-03-22 18:00 CDT
- **Branch context:** `master` for docs link review; active dev branch under watch: `develop/v2.0.6` (PR #81)
- **Reviewer:** OpenClaw

## 1. PR review status

### open-fdd PR #81
- PR: <https://github.com/bbartling/open-fdd/pull/81>
- Title: `Develop/v2.0.6`
- CI status:
  - `test` = pass
  - `CodeRabbit` = pass / review completed

### Current merge-readiness assessment
- **Status:** caution, nearly ready
- **Meaningful review items still standing:**
  1. disable container selector while log streaming is active
  2. guard stale async callbacks in stream handling
  3. pre-validate Docker/container existence before `follow=true` streaming so backend returns proper error status instead of streaming error text with 200

### Classification
- product polish / correctness work, not a blocker-level regression

## 2. Container-log monitoring status

### Docker access from this test bench
- `docker ps` failed because Docker Desktop Linux engine pipe was unavailable from this machine at review time
- This is currently a **testbench limitation**, not proof that the Open-FDD feature is broken

### Classification
- **testbench limitation**

## 3. BACnet / data-model verification

### Current Open-FDD modeled/exported state observed at 18:00 window start
- `GET /data-model/export?bacnet_only=true` showed a populated modeled test bench state, including:
  - site: `TestBenchSite`
  - equipment: `AHU-1`, `VAV-1`, `Weather-Station`
  - many AHU/VAV/weather points with Brick tags and polling enabled
- This state did **not** match the lean final intended model from the earlier user-guided modeling pass (`BensSuperTestBench` + minimal 5-point polling)

### SPARQL BACnet review
- SPARQL query confirmed device `3456789` and its BACnet objects in graph
- Current query output during this first nightly pass showed device `3456789` objects clearly; device `3456790` was expected from earlier work but the truncated sample at this moment only showed the first device bindings

### Interpretation
- Current state appears to have drifted from the latest intended minimal model and may reflect an earlier/larger modeling state restored in DB/graph
- This needs follow-up tonight before treating the current model as canonical

### Classification
- likely **setup drift** or DB state drift relative to intended minimal test configuration

## 4. Docs / link review

### Checked
- `master` docs homepage: <https://bbartling.github.io/open-fdd/> → loads
- `master` docs route for LLM workflow: <https://bbartling.github.io/open-fdd/modeling/llm_workflow/> → 404

### Notes
- This remains a real docs problem on `master`
- The repo/docs tree indicates LLM workflow content exists, so this is likely a published-route/config mismatch rather than missing source content

### Classification
- **documentation gap / docs-site bug**

## 5. Big-picture gaps reinforced during this pass

- container-log review is useful, but local bench access to Docker/runtime evidence is still weak
- overnight BACnet/FDD verification still needs a cleaner generated evidence artifact
- current modeled state can drift from intended minimal scope unless the overnight flow explicitly verifies site/equipment/point count and naming

## 6. Follow-up observation at 18:15 CDT

A second check during the nightly window showed the live model has concretely drifted back to a larger `TestBenchSite` configuration rather than the lean 5-point `BensSuperTestBench` state.

Observed at 18:15 CDT:
- `GET /sites` returned 1 site: `TestBenchSite`
- `GET /points` returned 39 points
- point set includes a much broader AHU/VAV/weather model with many `fdd_input` mappings and polling enabled

This confirms the nightly environment is currently **not** in the intentionally minimal polling state.

### Classification
- **setup drift** / live configuration drift relative to intended lean testbench model

## 7. Recommended next overnight steps

1. confirm which model is intended to remain live overnight: minimal `BensSuperTestBench` or the broader `TestBenchSite`
2. run raw BACnet read requests against selected points and compare with Open-FDD values
3. continue docs/link review on `master`
4. keep PR #81 under watch for new commits or responses to CodeRabbit comments

## 8. 19:00 window update

### PR #81
- no new commits since the earlier 14:14 CDT update
- `test` still passing
- CodeRabbit review still complete with the same 3 actionable stream/log issues

### BACnet graph/device counts
- SPARQL at 19:00 confirmed both BACnet devices are present in graph:
  - `3456789` @ `192.168.204.13` with **18** contained objects
  - `3456790` @ `192.168.204.14` with **7** contained objects
- DIY BACnet server RPC surface still reachable (`:8080` openapi OK)

### Model/config state
- live site still reads as `TestBenchSite`
- live point set remains broader than the intended lean 5-point test model
- this continues to look like **setup drift / live configuration drift** rather than a fresh product bug

### Docs
- `master` LLM workflow docs route still 404s

## 9. 19:30 window update

### Live API/model state unchanged
- `GET /sites` still returns 1 site: `TestBenchSite`
- `GET /points` still returns 39 points
- current live model remains the broader AHU/VAV/weather configuration, not the intended lean 5-point overnight scope
- classification remains **setup drift / live configuration drift**

### PR #81 unchanged
- `test` still passing
- CodeRabbit review still complete
- no new commits or status changes since earlier nightly checks

### Dashboard/tooling note
- local Dash dashboard at `127.0.0.1:8051` is currently down again
- this is a **tooling stability limitation** for the local helper app, not an Open-FDD product finding

## 10. 20:00 docs comb update

### Confirmed broken/bad links
- live docs route still broken on `master`:
  - `https://bbartling.github.io/open-fdd/modeling/llm_workflow/` → 404
- stale GitHub file link remains broken:
  - `https://github.com/bbartling/open-fdd/blob/master/pdf/canonical_llm_prompt.txt` → 404

### Confirmed good links
- docs homepage loads:
  - `https://bbartling.github.io/open-fdd/`
- PDF link exists:
  - `https://github.com/bbartling/open-fdd/blob/master/pdf/open-fdd-docs.pdf`

### Classification
- **documentation gap / broken reference**
- issue already captured earlier; no new docs issue needed from this pass
