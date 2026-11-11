# CHOAM

**Commerce, with rules.** Agentic commerce infrastructure with deterministic authorization boundaries.

## Current capabilities

- Deterministic purchase-intent preview and explicit buyer confirmation.
- Version-checked buyer bearer authorization. The plaintext token is returned once at request creation; only its SHA-256 digest is stored.
- Buyer/seller offer history with optimistic version checks.
- Deterministic purchase-integrity evaluation and database constraints.
- PayPal sandbox order creation and capture for accepted offers.
- Transactional audit events for request, negotiation, and payment state changes.
- Read-only MCP server for purchase preview, buyer-authorized request/offer inspection, and integrity checks.

## Run locally with Docker Compose

1. Copy `.env.example` to `.env` in the repository root.
2. Run `docker compose up --build`.
3. Open the frontend at `http://localhost:3000`.
4. Check API liveness at `http://localhost:8000/api/v1/health` and readiness at `http://localhost:8000/api/v1/ready`.

PostgreSQL data is persisted in the `choam-postgres` Docker volume. The backend applies Alembic migrations before starting. PayPal sandbox credentials are optional until you test the payment flow.

## Local development without Docker

Backend: `cd backend && pip install -e '.[dev]' && alembic upgrade head && uvicorn app.main:app --reload`

Frontend: `cd frontend && npm install && npm run dev`

Python 3.11+, Node 20+ and PostgreSQL 15+ are expected. Copy `.env.example` to `backend/.env` and set `DATABASE_URL`.

## MCP server

Install backend dependencies, then run `cd backend && choam-mcp` (or `python -m app.mcp.server`). The server uses stdio and exposes four tools: `preview_purchase_intent`, `get_purchase_request`, `list_negotiation_offers`, and `check_purchase_integrity`. The three request-specific tools require the buyer access token. MCP tools are read-only; state-changing operations remain behind the version-checked HTTP API.

## PayPal sandbox

Set `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` in the root `.env` file for Docker Compose, or in the backend environment. The default API host is PayPal's sandbox endpoint. Never use live credentials in local development.

After a request reaches `accepted`, create a payment with `POST /api/v1/purchase-requests/{request_id}/payments`, supplying `X-Buyer-Authorization`, `Idempotency-Key`, and `expected_request_version`. Redirect the buyer to the returned `approval_url`. Once approved in PayPal, call `POST /api/v1/purchase-requests/{request_id}/payments/{payment_id}/capture` with the buyer token and current request version.

Payment capture is only marked successful when PayPal returns `COMPLETED` and a capture ID. This is a sandbox integration; webhook verification, refunds, disputes, production credential handling, and reconciliation are not implemented.

## Security boundaries

Seller identity is not yet verified: seller-role actions are recorded as claimed roles, not authenticated seller accounts. Buyer bearer tokens are high-entropy one-time credentials and must be treated as secrets. Audit rows are append-only by application convention, not cryptographically tamper-evident or protected against privileged database modification.

CHOAM is a working name. Naming and trademark clearance is required before launch; this project is not affiliated with or endorsed by the Dune franchise.
