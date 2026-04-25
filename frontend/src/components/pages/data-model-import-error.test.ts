import { describe, expect, it } from "vitest";

import {
  firstImportValidationFailure,
  formatValidationPath,
} from "@/components/pages/data-model-import-error";

describe("data-model import error helpers", () => {
  it("formats nested validation paths with array indexes", () => {
    expect(formatValidationPath(["body", "points", 0, "equipment_type"])).toBe(
      "points[0].equipment_type",
    );
  });

  it("extracts first validation failure from API payload", () => {
    const payload = {
      error: {
        code: "VALIDATION_ERROR",
        message: "Request validation failed",
        details: {
          errors: [
            {
              loc: ["body", "equipment", 1, "bogus_field"],
              msg: "Extra inputs are not permitted",
              type: "extra_forbidden",
            },
          ],
        },
      },
    };
    expect(firstImportValidationFailure(payload)).toEqual({
      path: "equipment[1].bogus_field",
      message: "Extra inputs are not permitted",
    });
  });

  it("falls back to error type when msg is empty", () => {
    const payload = {
      error: {
        details: {
          errors: [
            {
              loc: ["body", "equipment", 1, "bogus_field"],
              msg: "",
              type: "extra_forbidden",
            },
          ],
        },
      },
    };
    expect(firstImportValidationFailure(payload)).toEqual({
      path: "equipment[1].bogus_field",
      message: "extra_forbidden",
    });
  });
});
