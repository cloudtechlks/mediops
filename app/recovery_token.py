"""Public verification only. The signing key is held exclusively by Jam."""
import base64
import json
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def decode(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def verify_token(token, public_key, account, now=None):
    if not isinstance(token, str) or len(token) > 4096:
        raise ValueError("Invalid recovery token")
    try:
        payload, signature = token.split(".")
        Ed25519PublicKey.from_public_bytes(decode(public_key)).verify(decode(signature), payload.encode("ascii"))
        claims = json.loads(decode(payload))
        now = int(time.time()) if now is None else now
        if (claims.get("aud") != "mediops-recovery" or claims.get("account") != account
                or not isinstance(claims.get("exp"), int) or not isinstance(claims.get("iat"), int)
                or claims["iat"] > now + 30 or claims["exp"] <= now
                or claims["exp"] - claims["iat"] > 14400):
            raise ValueError("Invalid recovery token")
        return claims
    except Exception as exc:
        raise ValueError("Invalid or expired recovery token") from exc
