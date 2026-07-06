import { describe, expect, it } from "vitest";
import { assertNoSensitiveMaterial } from "../src/index.js";

describe("Access safety", () => {
  it("rejects Bitcoin seed and private key-looking input", () => {
    expect(() => assertNoSensitiveMaterial({ bitcoin_seed: "abandon abandon abandon" })).toThrow();
    expect(() => assertNoSensitiveMaterial({ private_key: "xprv123" })).toThrow();
  });
});
