# ruff: noqa: E501
"""SP1 WebCrypto signing boundary; private CryptoKeys never enter Python State."""

from __future__ import annotations

import json
from typing import Protocol


class DeviceProviderUnavailable(RuntimeError):
    pass


class DeviceSigningProvider(Protocol):
    @property
    def device_public_key(self) -> str: ...

    @property
    def device_key_fingerprint(self) -> str: ...

    async def sign_access_challenge(self, canonical_payload: str) -> str: ...


class UnavailableDeviceProvider:
    @property
    def device_public_key(self) -> str:
        raise DeviceProviderUnavailable("secure_device_provider_unavailable")

    @property
    def device_key_fingerprint(self) -> str:
        raise DeviceProviderUnavailable("secure_device_provider_unavailable")

    async def sign_access_challenge(self, canonical_payload: str) -> str:
        del canonical_payload
        raise DeviceProviderUnavailable("secure_device_provider_unavailable")


def device_identity_script() -> str:
    """Return browser JS which loads/creates a non-extractable Ed25519 key."""
    return """
    (async () => {
      if (!globalThis.crypto?.subtle || !globalThis.indexedDB) {
        return {ok:false, error:'secure_device_provider_unavailable'};
      }
      try {
        const db = await new Promise((resolve, reject) => {
          const req = indexedDB.open('bitcoin-bastion-access-device-v1', 1);
          req.onupgradeneeded = () => req.result.createObjectStore('keys');
          req.onsuccess = () => resolve(req.result); req.onerror = () => reject(req.error);
        });
        let pair = await new Promise((resolve, reject) => {
          const req = db.transaction('keys').objectStore('keys').get('issuance-ed25519');
          req.onsuccess = () => resolve(req.result); req.onerror = () => reject(req.error);
        });
        if (!pair) {
          pair = await crypto.subtle.generateKey({name:'Ed25519'}, false, ['sign','verify']);
          await new Promise((resolve, reject) => {
            const req = db.transaction('keys','readwrite').objectStore('keys').put(pair, 'issuance-ed25519');
            req.onsuccess = () => resolve(); req.onerror = () => reject(req.error);
          });
        }
        if (pair.privateKey.extractable) throw new Error('extractable_private_key_rejected');
        const spki = new Uint8Array(await crypto.subtle.exportKey('spki', pair.publicKey));
        const b64 = btoa(String.fromCharCode(...spki));
        const pem = '-----BEGIN PUBLIC KEY-----\\n' + (b64.match(/.{1,64}/g)||[]).join('\\n') +
          '\\n-----END PUBLIC KEY-----\\n';
        const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', spki));
        const fingerprint = 'sha256:' + [...digest].map(x => x.toString(16).padStart(2,'0')).join('');
        return {ok:true, device_public_key:pem, device_key_fingerprint:fingerprint};
      } catch (_) { return {ok:false, error:'secure_device_provider_unavailable'}; }
    })()
    """


def sign_challenge_script(canonical_payload: str) -> str:
    """Sign the exact backend canonical JSON using the persisted CryptoKey."""
    payload = json.dumps(canonical_payload)
    return f"""
    (async () => {{
      try {{
        const db = await new Promise((resolve, reject) => {{
          const req = indexedDB.open('bitcoin-bastion-access-device-v1', 1);
          req.onsuccess = () => resolve(req.result); req.onerror = () => reject(req.error);
        }});
        const pair = await new Promise((resolve, reject) => {{
          const req = db.transaction('keys').objectStore('keys').get('issuance-ed25519');
          req.onsuccess = () => resolve(req.result); req.onerror = () => reject(req.error);
        }});
        if (!pair || pair.privateKey.extractable) return {{ok:false,error:'secure_device_provider_unavailable'}};
        const message = new TextEncoder().encode('BastionProofOfAccess:v1:access_challenge\\n' + {payload});
        const raw = new Uint8Array(await crypto.subtle.sign({{name:'Ed25519'}}, pair.privateKey, message));
        const signature = btoa(String.fromCharCode(...raw)).replaceAll('+','-').replaceAll('/','_').replace(/=+$/,'');
        return {{ok:true, signature}};
      }} catch (_) {{ return {{ok:false,error:'device_signing_failed'}}; }}
    }})()
    """
