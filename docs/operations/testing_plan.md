---
title: Testing plan
parent: Operations
nav_order: 7
---

# Testing plan

This is the evolving engineering plan for Open-FDD automated testing and the optional **OpenClaw lab** bench under [`openclaw/README.md`](https://github.com/bbartling/open-fdd-afdd-stack/tree/main/openclaw/README.md).

## OpenClaw continuation prompt (sibling-container bench)

Use this when OpenClaw is running as a sibling Docker container and you want it to continue after network wiring fixes:

```text
Continue the focused regression + soak on the current Open-FDD bench run.

Runtime + Access
- You are running as a sibling Docker container on the same host as Open-FDD.
- Do not use local filesystem paths like /home/ben/... .
- Primary base URL: http://openfdd_api:8000
- Fallback base URL: http://host.docker.internal:8000
- Health endpoint: GET /health
- Auth: X-API-Key: <ROTATED_API_KEY>

Preflight (must pass before phase work)
1) GET /health
2) GET /config
3) GET /model-context/docs?query=openclaw+sibling+docker+openfdd_api+host.docker.internal&mode=excerpt&max_chars=28000
4) GET /mcp/manifest

Phases to execute
- Phase 1: Preconditions and config capture
- Phase 1.5: Validate MCP/doc context includes sibling-container networking guidance
- Phase 2: Discovery + baseline model export
- Phase 3: Deterministic fault emission gate
- Phase 4: AI-assisted import validation (valid + invalid nested key + relationship edits)
- Phase 5: YAML rule lifecycle add/remove
- Phase 6: Overnight soak (scrape + FDD loops, stability tracking)

Pass criteria
- openfdd_api reachability remains stable
- deterministic expected fault emits with clear equipment attribution
- strict 422 validation behavior is correct on invalid import variant
- MCP/docs reflect internal networking guidance for sibling-container mode
- no critical runtime instability during soak

Deliverables
- one-page summary
- phase-by-phase pass/fail with evidence
- blocker list with repro steps
- prioritized patch recommendations
- artifact index (model exports, import payloads/responses, SPARQL results, logs, MCP/docs validation outputs)
```

## Near-term priorities

### 0. Continuous PR and CI review

The OpenClaw workflow should continuously watch active PRs in the same spirit as CodeRabbit:

- detect new commits quickly
- re-check CI and review state
- inspect changed files directly
- run targeted local checks where possible
- write down risks, limitations, and next tests instead of relying on chat memory

See [AI PR review playbook](../appendix/ai_pr_review_playbook).

### Daytime short-run counterpart

The overnight suite should have a daytime counterpart that exercises the same major paths without taking the full 12-hour window.

Current recommended shape:

- keep E2E, SPARQL/frontend parity, hot-reload, and BACnet/FDD checks
- use a shorter BACnet scrape profile that stays under 2 hours total
- use this as a daytime confidence pass before the real overnight run

Example:

```bash
python openclaw/bench/e2e/automated_suite.py \
  --api-url http://HOST:8000 \
  --frontend-url http://HOST \
  --long-run-check-faults \
  --long-run-short-day
```

Or on Windows: [`openclaw/windows/run_daytime_short_suite.cmd`](https://github.com/bbartling/open-fdd-afdd-stack/tree/main/openclaw/windows/run_daytime_short_suite.cmd) (edit URLs first).

### 1. Keep authenticated backend graph checks healthy

Latest status:

- direct authenticated backend access has been restored on the current bench context
- `GET /data-model/check` and authenticated `POST /data-model/sparql` are now working again

Ongoing risk:

- auth still depends on the real launch context, not just a remembered file location
- future overnight runs can regress back into auth/config drift if the bench shell or Python context loses `OFDD_API_KEY`
- the current `/data-model/sparql` response shape may be `{"bindings": [...]}` in some environments, so tooling should not assume strict SPARQL JSON `results.bindings`

Action:

- keep verifying that `OFDD_API_KEY` is available to the actual automated testing environment before overnight runs
- make SPARQL-parsing code tolerant to both `bindings` and `results.bindings`
- keep treating backend auth failure as a pre-overnight readiness issue, not a product regression by default

Why it matters:

- without authenticated SPARQL/API access, BACnet graph validation is incomplete
- without response-shape tolerance, a healthy graph can be misclassified as empty

### 2. Promote BACnet addressing to a first-class validation target

We need to explicitly validate:

- BACnet devices in the graph
- device instance and address visibility
- object identifiers for polling points
- semantic equipment type for those points

This is no longer optional background metadata. It is core operational context.

### 3. Prove fault calculation from end to end

The target standard is:

- fake BACnet device fault schedule is known
- DIY BACnet server RPC confirms source values
- Open-FDD data-model SPARQL queries confirm BACnet devices and point addressing
- Open-FDD scrape path receives those values
- YAML rules + rolling windows predict an expected fault
- Open-FDD fault outputs show that exact fault
- the overnight process writes a durable report

See [BACnet-to-fault verification](../bacnet/fault_verification) and the report template at `openclaw/reports/overnight-bacnet-verification-template.md` in the repo (not on GitHub Pages).

### 4. Preserve reusable context for future clones

The repo should keep visible documentation and machine-readable operator policy for:

- the operational states
- overnight review discipline
- BACnet graph context
- portability assumptions
- future optimization intent
- documentation guidance that works for both humans and AI agents

### 5. Add nightly docs and link review

The overnight workflow should also:

- validate important README and docs links
- make sure link checking is done against the correct target branches
- treat `master` as the primary target branch
- optionally check one active development branch when it is the intended docs destination for unreleased fixes
- avoid mixing findings from unrelated feature branches
- identify missing docs pages or thin areas
- suggest documentation improvements that make the system easier for both humans and AI agents to understand
- record those suggestions in durable repo docs or review notes

## Future role in live HVAC systems

In a live HVAC deployment, the same testing and validation assets should support:

- confidence in FDD outputs
- confidence in model/rule applicability
- future optimization and supervisory logic
- operator- or facility-manager-facing monitoring summaries

The repo is not only a test harness. It is becoming a reproducible engineering context pack.
