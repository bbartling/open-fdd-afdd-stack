---
title: OpenClaw, Docker BACnet, and human data modeling
parent: How-to Guides
nav_order: 18
---

# OpenClaw, Docker BACnet, and human data modeling

This page is written for **OpenClaw** (and similar agents) that run **inside Docker** on the same Compose project as Open-FDD, and for **operators** doing **AI-assisted Brick tagging** in the browser. It is indexed into the optional **MCP RAG** corpus when you bootstrap with `--with-mcp-rag` (see [MCP RAG service](../operations/mcp_rag_service)).

---

## 1) BACnet driver topology

After Phase 2.5d, BACnet is handled by the embedded [rusty-bacnet](https://github.com/jscott3201/rusty-bacnet) driver — a PyO3 wrapper over a Rust ASHRAE 135-2020 stack. Both the API and the scraper containers load the driver in-process; there is **no separate gateway container** and **no HTTP JSON-RPC middle layer**.

- **`bacnet-scraper`** runs with **`network_mode: host`** so the driver can bind UDP/47808 on the host NIC that reaches the BAS.
- **`api`** runs on the normal Docker bridge; its `/bacnet/*` routes open a **per-request** `BipTransport` instance. If your build topology prevents the API container from reaching the BAS network (bridge-only), move the API to `network_mode: host` too or delegate ad-hoc reads to the scraper container.
- There is no `bacnet-server` container, no `host.docker.internal:8080` hairpin, and no `OFDD_BACNET_SERVER_URL` env var. Operators who remember those from earlier versions can ignore them.

The **Data Model BRICK** page in the React app is the primary human tagging UI. It assumes devices and objects already exist as graph nodes in SeleneDB (from discovery) and lets the operator bind points to objects.

---

## 2) Agents on the Docker bridge → API → rusty-bacnet

OpenClaw (or any external agent) talks to the Open-FDD **API** — never directly to the BACnet network. The agent flow is:

1. **Authenticate.** `OFDD_API_KEY` in the agent's env; send `Authorization: Bearer <key>` on every call.
2. **Discover devices.** `POST /bacnet/whois_range` with an optional instance range. The response contains one entry per I-Am responder. Each device is upserted into SeleneDB as a `:bacnet_device` node.
3. **Enumerate objects.** `POST /bacnet/point_discovery_to_graph` with `{"instance": {"device_instance": N}}`. The API reads the device's `object-list`, optionally enriches each object with `object-name` / `description` / `units`, and writes one `:bacnet_object` node per entry (linked to the device via `exposesObject`).
4. **Author points.** Use the Sites / Equipment / Points CRUD API to create application-layer points (with `brick_type`, `fdd_input`, etc.).
5. **Bind objects to points.** Internal Python API only for now: `openfdd_stack.platform.bacnet.graph.bind_object_to_point(...)`. A dedicated HTTP endpoint is a future slice.

The scrape loop walks `:bacnet_object -[:protocolBinding]-> :point` every `OFDD_BACNET_SCRAPE_INTERVAL_MIN` minutes and writes samples with `entity_id = point.id` via SeleneDB `ts_write`.

---

## 3) Firewall / routing expectations

Because the driver is in-process, there's no HTTP port to firewall. The relevant exposure is UDP/47808 on the scraper's host network.

- **Linux host:** ensure `ufw` / `iptables` allow outbound UDP/47808 on the OT NIC, and inbound unicast responses on the same NIC. When using `network_mode: host`, Docker bypasses its NAT tables for this container.
- **Dual-NIC edge devices:** set `OFDD_BACNET_INTERFACE` to the OT-side IPv4 so the driver binds only there. Leaving it at `0.0.0.0` binds every interface (acceptable for lab use; consider the IT-side exposure risk in production).
- **BBMD / Foreign Device:** rusty-bacnet supports BBMD registration; configure via `BACnetClient` kwargs if the BAS requires it. Wire that through `BipTransport` when your site hits a BBMD-gated network.

---

## 4) Human tagging flow (no agent)

An operator who prefers to drive the UI:

1. Open the **Data Model BRICK** page.
2. Create a site via the Sites CRUD API if needed.
3. Call `POST /bacnet/whois_range` from Swagger at `/docs` (or `curl`) to list devices.
4. For each device, call `POST /bacnet/point_discovery_to_graph`.
5. Back in the Data Model page, create equipment + points with BACnet context (`bacnet_device_id`, `object_identifier`, `object_name`), then Export JSON → LLM tag → Import.

The graph round-trip stays in SeleneDB; no TTL file edit is required.

---

## 5) Troubleshooting

- **API `/bacnet/server_hello` returns 401/403:** the API is up but Bearer auth is enforced; check `OFDD_API_KEY`.
- **API `/bacnet/whois_range` returns 502 with `BacnetTimeoutError`:** the driver is loaded but nothing responded within `OFDD_BACNET_APDU_TIMEOUT_MS`. Likely causes: wrong `OFDD_BACNET_BROADCAST_ADDRESS` for the subnet, or the API container is bridged and can't reach the BAS LAN. Move to `network_mode: host` or route a secondary NIC in.
- **Scraper logs "load_scrape_plan failed":** the scraper couldn't reach Selene. Check the `selene` container is healthy (`docker logs openfdd_selene`) and `OFDD_SELENE_URL` is reachable from the scraper.
- **Scraper writes zero samples:** no `:protocolBinding` edges exist yet. Run discovery then create bindings.

See also [BACnet overview](../bacnet/overview) for the architectural story, [Configuration](../configuration) for the env surface, and [Verification](verification) for health checks.
