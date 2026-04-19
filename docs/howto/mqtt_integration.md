---
title: MQTT integration (optional)
parent: How-to Guides
nav_order: 3
---

# MQTT integration (optional)

Open-FDD does **not** require MQTT for core FDD, BACnet scraping, or the web UI. MQTT is **optional** scaffolding for future edge/automation integrations. The legacy BACnet2MQTT and MQTT RPC gateway features rode on `diy-bacnet-server`; both were retired in Phase 2.5d along with the gateway itself.

## What the stack can do today

**Mosquitto (optional broker)**

Run `./scripts/bootstrap.sh --with-mqtt-bridge` to start a broker on **`localhost:1883`** (see [Getting started](../getting_started) and [Quick reference](quick_reference)). The broker is a standalone component today — nothing in the current BACnet driver publishes to it. Use it when you build a future integration (e.g. a publish-to-MQTT webhook on scrape writes, a Home Assistant discovery feed) or to prototype.

## Planned / future integrations

None of these are wired yet, but the broker is ready when a slice lands:

- **BACnet → MQTT publisher.** A thin service that tails `ts_write` events from SeleneDB (or piggybacks on the scraper's `ScrapeResult`) and publishes per-point state on configurable topics.
- **Home Assistant discovery feed.** Same publisher, with HA discovery payloads under `homeassistant/sensor/<point>/config`.
- **MQTT RPC gateway.** Optional alternative to the HTTP API for low-bandwidth / edge setups. Would accept command topics (`read_property`, `write_property`) and emit acks.

## Open-FDD product scope

- The data path is **embedded rusty-bacnet → SeleneDB `ts_write`**. No RPC middle layer.
- MQTT stays strictly additive. Nothing in the core read/write/scrape flow depends on a broker.

## Related docs

- [Getting started](../getting_started) — `--with-mqtt-bridge`
- [Quick reference](quick_reference) — broker port and status checks
- [BACnet overview](../bacnet/overview) — driver and scraper architecture
