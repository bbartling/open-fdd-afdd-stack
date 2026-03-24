# Overnight Summary — 2026-03-23 evening seed

- **Snapshot time:** 2026-03-23 18:48 CDT
- **Window:** Open-FDD dev-testing window (18:00–06:00 CDT)
- **Reviewer:** OpenClaw

## Executive summary

Early overnight checks show a mixed but improved state:

- direct authenticated backend SPARQL is working from this host now
- Docker/container log review is still blocked from this host because Docker Desktop Linux engine pipe is unavailable
- published docs home still loads, but the trailing-slash `llm_workflow/` route still 404s while the no-trailing-slash variant works
- the active PR target changed since the morning review: the currently active PR is now **#83 `develop/v2.0.7` -> `master`**
- a first DIY BACnet gateway read attempt failed because the request shape used was not the API’s expected JSON-RPC shape, which is a tooling/API-contract gap rather than proof of BACnet failure

## Active PR status

### open-fdd PR #83
- URL: <https://github.com/bbartling/open-fdd/pull/83>
- Title: `Develop/v2.0.7`
- Base: `master`
- Updated: 2026-03-23T14:13:08Z
- Status: open, not draft

### Interpretation
- The active PR under review is no longer the earlier `develop/v2.0.6` PR referenced in older notes.
- Future overnight docs/review should use PR #83 as the active dev-branch context unless a newer PR supersedes it.

## Backend auth / graph checks

### Direct backend checks
- authenticated `POST /data-model/sparql` returned **200**
- sample site query returned one site binding:
  - `http://openfdd.local/site#site_c6fd9156_7591_4840_ad23_15e78588dfe5`

### Interpretation
- The daytime auth-path fix appears to be holding for direct backend SPARQL access.
- This materially improves overnight trust compared with the earlier blanket-401 state.

### Classification
- **improved auth/config state**

## Docs link check

### Checked
- docs home: <https://bbartling.github.io/open-fdd/> -> 200
- LLM workflow trailing slash: <https://bbartling.github.io/open-fdd/modeling/llm_workflow/> -> 404
- LLM workflow no trailing slash: <https://bbartling.github.io/open-fdd/modeling/llm_workflow> -> 200
- docs PDF link: <https://github.com/bbartling/open-fdd/blob/master/pdf/open-fdd-docs.pdf> -> 200

### Interpretation
- The published docs route fragility for `llm_workflow` still exists.
- This remains a **documentation gap / route inconsistency**.

## Container/runtime evidence

### Docker access from this host
Attempted:
- `docker ps --format ...`

Observed:
- Docker Desktop Linux engine pipe unavailable:
  - `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`

### Interpretation
- Live container log review for `api`, `frontend`, `bacnet-scraper`, `fdd-loop`, `host-stats`, `bacnet-server` is still blocked from this host.

### Classification
- **testbench limitation**

## BACnet / gateway note

### First read attempt
A first POST to the DIY BACnet gateway `client_read_property` route returned JSON-RPC validation errors indicating the request body shape was wrong.

### Follow-up contract check and corrected read
The gateway OpenAPI confirmed that `client_read_property` expects a JSON-RPC envelope with `jsonrpc`, `id`, `method`, and `params.request`.

A corrected live read then succeeded:
- endpoint: `POST http://192.168.204.16:8080/client_read_property`
- request target: device `3456790`, object `analog-value,1`, property `present-value`
- result: `{"jsonrpc":"2.0","result":{"present-value":72.0},"id":1}`

Interpretation:
- the DIY BACnet gateway is reachable
- BACnet-side live reads are working when the request uses the correct JSON-RPC envelope
- the earlier failure was a **tooling/request-shape mistake**, not evidence that BACnet-side reads were broken

### Classification
- **tooling / API-contract mismatch corrected**
- **BACnet-side read path confirmed working**

## Current overnight stance

### Improved
- backend auth/SPARQL access is in a better place than earlier today

### Still weak
- container evidence unavailable from this host
- docs route inconsistency still present
- end-to-end fault-calculation proof is still not closed yet even though BACnet-side independent reads now work

## Highest-value next steps tonight

1. use the corrected JSON-RPC gateway contract for additional live BACnet reads on representative modeled points
2. continue targeted SPARQL/frontend parity isolation after the auth improvement
3. verify fault outputs against fake-device schedules now that BACnet-side independent evidence is in hand
4. keep using PR #83 as the active dev-branch review context
