export type OverviewTabGuide = {
  label: string;
  purpose: string;
  whenToUse: string;
};

export const OVERVIEW_TAB_GUIDE: OverviewTabGuide[] = [
  {
    label: "OpenFDD Config",
    purpose: "Set loop timing, BACnet/weather behavior, and graph sync defaults.",
    whenToUse: "Visit first after install or after restoring from backup.",
  },
  {
    label: "BACnet tools",
    purpose: "Run discovery/read/write checks against BACnet gateways.",
    whenToUse: "Use when validating live connectivity and object-level responses.",
  },
  {
    label: "Data Model BRICK",
    purpose: "Export/import model JSON and manage Brick + BACnet mapping.",
    whenToUse: "Use before upgrades for backup, and after resets for restore.",
  },
  {
    label: "Points",
    purpose: "Review point inventory, polling flags, and basic CRUD operations.",
    whenToUse: "Use while refining scrape scope and point quality.",
  },
  {
    label: "Faults",
    purpose: "Inspect active faults, fault definitions, and rule file lifecycle.",
    whenToUse: "Use for rule tuning and fault triage.",
  },
  {
    label: "Plots",
    purpose: "Trend selected points/fault overlays and manage timeseries hygiene.",
    whenToUse: "Use for visual checks, CSV export, and timeseries purge actions.",
  },
  {
    label: "Weather data",
    purpose: "Inspect Open-Meteo points and chart weather trends.",
    whenToUse: "Use when weather-driven rules are in scope.",
  },
  {
    label: "Analytics",
    purpose: "Review fault summary/timeseries and point analytics endpoints.",
    whenToUse: "Use for KPI reporting and historical diagnostics.",
  },
  {
    label: "System resources",
    purpose: "Inspect host/container metrics and runtime health context.",
    whenToUse: "Use when performance or reliability looks off.",
  },
];

export const OVERVIEW_QUICK_START = [
  "Select a site in the top bar, then open Data Model BRICK to export a JSON backup before major updates.",
  "For update cleanup while keeping model knowledge, use Plots → Purge timeseries (site-scoped) or bootstrap --purge-timeseries.",
  "If model data is intentionally reset, import the saved JSON for restore and polling/rule inputs resume without remapping every point.",
] as const;

export const MCP_NOTE =
  "MCP RAG is available when the stack is bootstrapped with --with-mcp-rag (service on :8090).";
