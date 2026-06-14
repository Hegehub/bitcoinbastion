import { createHmac, timingSafeEqual } from "node:crypto";

export interface VerifyWebhookSignatureOptions {
  payload: string | Buffer;
  signature: string;
  timestamp: string | number;
  secret: string;
  deliveryId?: string;
  eventType?: string;
  toleranceSeconds?: number;
}

export function verifyBastionWebhookSignature(options: VerifyWebhookSignatureOptions): boolean {
  const toleranceSeconds = options.toleranceSeconds ?? 300;
  const timestamp = Number(options.timestamp);
  const nowSeconds = Math.floor(Date.now() / 1000);
  if (!Number.isFinite(timestamp) || Math.abs(nowSeconds - timestamp) > toleranceSeconds) return false;
  if (!options.signature.startsWith("v1=") || !options.deliveryId || !options.eventType) return false;
  const rawPayload = Buffer.isBuffer(options.payload) ? options.payload.toString("utf8") : options.payload;
  const expected = `v1=${createHmac("sha256", options.secret).update(`${timestamp}.${options.deliveryId}.${options.eventType}.${rawPayload}`).digest("hex")}`;
  const expectedBuffer = Buffer.from(expected);
  const actualBuffer = Buffer.from(options.signature);
  return expectedBuffer.length === actualBuffer.length && timingSafeEqual(expectedBuffer, actualBuffer);
}
