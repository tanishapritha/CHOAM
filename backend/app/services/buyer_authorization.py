import hashlib
import secrets

from app.models.purchase_request import PurchaseRequest


def issue_buyer_token() -> tuple[str, str]:
    """Return a one-time plaintext bearer token and its SHA-256 storage digest."""
    token = secrets.token_urlsafe(32)
    return token, hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_buyer_token(request: PurchaseRequest, token: str | None) -> bool:
    if not token or not request.buyer_token_hash:
        return False
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return secrets.compare_digest(digest, request.buyer_token_hash)
