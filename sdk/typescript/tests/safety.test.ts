import { describe, expect, it } from "vitest";
import { BastionSafetyError, assertNoSensitiveMaterial, containsSensitiveMaterial } from "../src/index.js";

describe("safety", () => {
  for (const value of ["seed phrase", "mnemonic", "private key", "xprv", "yprv", "zprv", "wallet.dat", "keystore", "12 words", "24 words", "signing material"]) {
    it(`rejects ${value}`, () => {
      expect(containsSensitiveMaterial(value)).toBe(true);
      expect(() => assertNoSensitiveMaterial(value)).toThrow(BastionSafetyError);
    });
  }

  it("allows public Bitcoin address references", () => {
    expect(() => assertNoSensitiveMaterial("bc1qexamplepublicaddress000000000000000000000")).not.toThrow();
  });
});
