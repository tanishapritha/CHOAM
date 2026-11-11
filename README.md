# CHOAM

**Commerce, with rules.** Agentic commerce infrastructure with deterministic authorization boundaries.

## Current capabilities

- Deterministic purchase-intent preview and explicit buyer confirmation.
- Version-checked buyer bearer authorization. The plaintext token is returned once at request creation; only its SHA-256 digest is stored.
- Buyer/seller offer history with optimistic version checks.
- Deterministic purchase-integrity evaluation and database constraints.
- PayPal sandbox order creation and capture for accepted offers.

## Local development

Backend: `cd backend && pip install -e '.[dev]' && alembic upgrade head && uvicorn app.main:app --reload`

Frontend: `cd frontend && npm install && npm run dev`

Python 3.11+, Node 20+ and PostgreSQL 15+ are expected. Copy `.env.example` to `backend/.env` and set `DATABASE_URL`.

## PayPal sandbox

Set `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` in the backend environment. The default API host is PayPal's sandbox endpoint. Never use live credentials in local development.

After a request reaches `accepted`, create a payment with `POST /api/v1/purchase-requests/{request_id}/payments`, supplying `X-Buyer-Authorization`, `Idempotency-Key`, and `expected_request_version`. Redirect the buyer to the returned `approval_url`. Once approved in PayPal, call `POST /api/v1/purchase-requests/{request_id}/payments/{payment_id}/capture` with the buyer token and current request version.

Payment capture is only marked successful when PayPal returns `COMPLETED` and a capture ID. This is a sandbox integration; webhook verification, refunds, disputes, production credential handling, and reconciliation are not implemented.

CHOAM is a working name. Naming and trademark clearance is required before launch; this project is not affiliated with or endorsed by the Dune franchise.
