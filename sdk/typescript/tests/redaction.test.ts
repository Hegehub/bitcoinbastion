import { describe, expect, it } from "vitest";
import { redactAccessPass, redactSensitiveObject, redactSessionToken, redactSignature } from "../src/index.js";

describe("redaction", () => {
  it("redacts raw Access Passes", () => {
    expect(redactAccessPass("bbp_live_abcdef123456")).not.toContain("abcdef123456");
    expect(redactAccessPass("bbp_live_abcdef123456")).toBe("bbp_live_...3456");
  });

  it("redacts session tokens and signatures", () => {
    expect(redactSessionToken("sess_abcdef123456")).toBe("sess_...3456");
    expect(redactSignature("sig_abcdef123456")).toBe("sig_...3456");
  });

  it("redacts nested sensitive objects and arrays", () => {
    const redacted = redactSensitiveObject({
      Authorization: "Bearer token",
      nested: [{ sessionToken: "sess_secret" }, { ok: true }],
      private_key: "secret",
    });
    expect(JSON.stringify(redacted)).not.toContain("Bearer token");
    expect(JSON.stringify(redacted)).not.toContain("sess_secret");
    expect(JSON.stringify(redacted)).not.toContain("secret");
  });
});
