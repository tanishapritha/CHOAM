from types import SimpleNamespace

from app.services.buyer_authorization import issue_buyer_token, verify_buyer_token


def test_buyer_token_is_stored_as_hash_and_verifies():
    token, token_hash = issue_buyer_token()
    request = SimpleNamespace(buyer_token_hash=token_hash)
    assert token not in token_hash
    assert verify_buyer_token(request, token)


def test_missing_or_wrong_buyer_token_is_rejected():
    request = SimpleNamespace(buyer_token_hash="a" * 64)
    assert not verify_buyer_token(request, None)
    assert not verify_buyer_token(request, "incorrect-token")


def test_legacy_request_without_token_cannot_be_buyer_authorized():
    request = SimpleNamespace(buyer_token_hash=None)
    assert not verify_buyer_token(request, "any-token")
