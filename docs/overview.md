---
title: System Overview
nav_order: 2
---

# System Overview

**This repository** ships the **`open-fdd`** Python package on **PyPI**: YAML-defined **FDD rules on pandas** (`open_fdd.engine`), plus schema and reporting helpers. That engine can run **inside your own application** or inside the **AFDD Docker stack** (separate repo), which installs `open-fdd` from PyPI and adds TimescaleDB, scrapers, FastAPI, and a React UI.

The text below describes the **full edge platform** as deployed from **[open-fdd-afdd-stack](https://github.com/bbartling/open-fdd-afdd-stack)**—knowledge graph, services, and data flow. For engine-only usage, see **[Engine-only / IoT](howto/engine_only_iot)** and **[Getting started](getting_started)**.

---


## Architecture

![Open-FDD Edge Platform Architecture](https://raw.githubusercontent.com/bbartling/open-fdd/master/open-fdd-schematic.png)

This project is an open-source stack; a cloud or MSI vendor can develop their own Docker container and deploy it on the **same client-hosted server** that runs Open-FDD, pulling from the local API over the LAN. That approach removes the need for a separate IoT or edge device dedicated to the vendor.

---

## Services

| Service | Description |
|---------|-------------|
| **API** | FastAPI CRUD for sites, equipment, points. Data-model export/import, TTL generation, SPARQL validation. Swagger at `/docs`. Config UI (HA-style data model tree, BACnet test) at `/app/`. |
| **Grafana** | Pre-provisioned TimescaleDB datasource only (uid: openfdd_timescale). No dashboards; build your own with SQL from the [Grafana SQL cookbook](howto/grafana_cookbook). Use `--reset-grafana` to re-apply datasource provisioning. |
| **TimescaleDB** | PostgreSQL with TimescaleDB extension. Single source of truth for metadata and time-series. |
| **BACnet scraper** | Embedded [rusty-bacnet](https://github.com/jscott3201/rusty-bacnet) driver; binds UDP/47808 via `network_mode: host`. Reads `:bacnet_object → :point` bindings from SeleneDB and writes samples via `ts_write`. |
| **SeleneDB** | Graph + time-series + vector + RDF in one runtime. Holds BACnet discovery (`:bacnet_device` / `:bacnet_object`), application points, and scrape samples. |
| **Weather scraper** | Fetches from Open-Meteo ERA5 (temp, RH, dewpoint, wind, solar/radiation, cloud cover). |
| **FDD loop** | Runs every N hours (see `rule_interval_hours`, `lookback_days` in platform config). Pulls last N days from DB into pandas, **reloads all rules from YAML on every run** (hot reload), runs rules, writes `fault_results` back to DB. No restart needed when tuning rule params. |

---

## Campus-based architecture

![Open-FDD Edge Platform Architecture Campus](https://raw.githubusercontent.com/bbartling/open-fdd/master/open-fdd-schematic-bacnet-gateway.png)

Remote Open-FDD BACnet edges can be deployed **across each subnet** on the internal campus IT network. Typically each building has its own BACnet network on a unique subnet; one edge per building or per subnet keeps BACnet traffic local while forwarding data to a **centralized** Open-FDD instance (API, Grafana, FDD loop, database). That gives the campus a single integration point for the cloud-based vendor of choice — one API and one data model for the whole portfolio, without the vendor touching each building's BACnet network directly.

**How to set it up:** Each edge runs the stack in **collector mode** (`--mode collector`): `db`, `selene`, `bacnet-scraper`. The scraper binds UDP/47808 on the OT NIC via `network_mode: host` and writes discovery + samples to the local SeleneDB. Point the edge's Selene at the central Selene (federation arrives in a later slice; for now each edge is a self-contained sample store). Run the full API / FDD loop / Grafana on the central host, reading from the federated or replicated Selene dataset. Multi-site topologies that used to span `OFDD_BACNET_GATEWAYS` now return as `:bacnet_network` nodes in the graph — one node per edge — with `hasDevice` edges linking each site's devices.

---

## Data flow

1. **Ingestion:** BACnet scraper and weather scraper write to `timeseries_readings` (point_id, ts, value).
2. **Data model (unified graph):** The building is represented as a **unified graph**—one semantic model combining Brick (sites, equipment, points), BACnet discovery (`:bacnet_device` / `:bacnet_object` nodes from the embedded rusty-bacnet driver), platform config, and room for future ontologies (e.g. ASHRAE 223P). CRUD and **POST /bacnet/point_discovery_to_graph** update this model; SPARQL queries it. The TTL file `config/data_model.ttl` remains as a legacy export format; SeleneDB is the source of truth.
3. **FDD (Python/pandas):** The FDD loop pulls data into a pandas DataFrame, runs YAML rules, writes `fault_results` to the database. Fault logic lives in the rule runner; the database is read/write storage.
4. **Visualization:** Grafana queries TimescaleDB for timeseries and fault results.

---

## Ways to deploy

- **Docker Compose (AFDD stack):** In **[open-fdd-afdd-stack](https://github.com/bbartling/open-fdd-afdd-stack)**, run `./scripts/bootstrap.sh` (see **[stack docs](https://bbartling.github.io/open-fdd-afdd-stack/)**).
- **Minimal stack (BACnet-focused):** `./scripts/bootstrap.sh --minimal` in that repo — DB + SeleneDB + BACnet scraper; no full API/FDD/weather unless you add services.
- **Engine only:** `pip install open-fdd` and run `RuleRunner` on pandas DataFrames (no Compose); see **[Engine-only / IoT](howto/engine_only_iot)**.
- **Manual / custom:** Start your own processes; reuse the same rule YAML and `open_fdd.engine` APIs.

---

## Key concepts

- **Sites** — Buildings or facilities.
- **Equipment** — Devices (AHUs, VAVs, heat pumps). Belong to a site.
- **Points** — Time-series references. Have `external_id` (raw name), `rule_input` (FDD column ref), optional `brick_type` (Brick class).
- **Fault rules** — YAML files (bounds, flatline, hunting, expression). Run against DataFrame; produce boolean fault flags. See [Fault rules for HVAC](rules/overview).
- **Unified graph** — One semantic model (Brick + BACnet + platform config; future 223P or other ontologies). Stored in `config/data_model.ttl`; maps Brick classes → `external_id` for rule resolution; queryable via SPARQL.
