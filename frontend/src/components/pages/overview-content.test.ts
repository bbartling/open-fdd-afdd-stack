import { describe, expect, it } from "vitest";

import { MCP_NOTE, OVERVIEW_QUICK_START, OVERVIEW_TAB_GUIDE } from "@/components/pages/overview-content";

describe("overview-content", () => {
  it("includes guide rows for key operator tabs", () => {
    const labels = new Set(OVERVIEW_TAB_GUIDE.map((r) => r.label));
    expect(labels.has("OpenFDD Config")).toBe(true);
    expect(labels.has("Data Model BRICK")).toBe(true);
    expect(labels.has("Plots")).toBe(true);
    expect(labels.has("Faults")).toBe(true);
  });

  it("contains update/restore workflow hints", () => {
    expect(OVERVIEW_QUICK_START.length).toBeGreaterThanOrEqual(3);
    expect(OVERVIEW_QUICK_START.join(" ")).toContain("export");
    expect(OVERVIEW_QUICK_START.join(" ")).toContain("restore");
  });

  it("mentions MCP bootstrap behavior", () => {
    expect(MCP_NOTE).toContain("--with-mcp-rag");
  });
});
