import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetchMock = vi.fn();

vi.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetchMock(...args),
}));

import { purgeTimeseries } from "@/lib/crud-api";

describe("purgeTimeseries", () => {
  beforeEach(() => {
    apiFetchMock.mockReset();
    apiFetchMock.mockResolvedValue({ status: "ok", deleted_rows: 0 });
  });

  it("posts purge with site_id when provided", async () => {
    await purgeTimeseries("site-123");
    expect(apiFetchMock).toHaveBeenCalledWith("/timeseries/purge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ site_id: "site-123" }),
    });
  });

  it("posts purge-all when site_id omitted", async () => {
    await purgeTimeseries();
    expect(apiFetchMock).toHaveBeenCalledWith("/timeseries/purge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
  });
});
