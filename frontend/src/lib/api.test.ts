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
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
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

    try {
      await apiFetch("/data-model/import", { method: "PUT" });
      expect.unreachable("Expected apiFetch to throw");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).status).toBe(422);
      expect((err as ApiError).message).toContain("422");
      expect((err as ApiError).payload).toEqual(
        expect.objectContaining({
          error: expect.any(Object),
        }),
      );
    }
  });
});
