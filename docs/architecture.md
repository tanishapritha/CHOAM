# Architecture

CHOAM is a modular monolith. FastAPI owns business logic and persistence; PostgreSQL is the source of truth. The frontend is a presentation layer and must never authorize payment.

Agent outputs and vendor messages are untrusted input. Deterministic integrity and authorization services own transaction decisions. Browser redirects are not proof of payment capture.

Planned backend modules: auth, requests, vendors, agents, negotiation, agreements, integrity, approvals, payments, webhooks, audit and MCP.
