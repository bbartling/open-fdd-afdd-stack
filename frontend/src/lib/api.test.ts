import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth", () => ({
  clearAuthTokens: vi.fn(),
  getAccessToken: vi.fn(() => null),
  setAccessToken: vi.fn(),
}));

import { ApiError, apiFetch } from "@/lib/api";

describe("apiFetch errors", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("throws ApiError with raw JSON payload", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      new Response(
        JSON.stringify({
          error: {
            code: "VALIDATION_ERROR",
            message: "Request validation failed at points[0].unknown_field: Extra inputs are not permitted",
            details: {
              errors: [
                {
                  loc: ["body", "points", 0, "unknown_field"],
                  msg: "Extra inputs are not permitted",
                  type: "extra_forbidden",
                },
              ],
            },
          },
        }),
        {
          status: 422,
          headers: { "content-type": "application/json" },
        },
      ),
    );

    await expect(apiFetch("/data-model/import", { method: "PUT" })).rejects.toBeInstanceOf(
      ApiError,
    );
    await expect(apiFetch("/data-model/import", { method: "PUT" })).rejects.toMatchObject({
      status: 422,
      message: expect.stringContaining("422"),
      payload: expect.objectContaining({
        error: expect.any(Object),
      }),
    });
  });
});
