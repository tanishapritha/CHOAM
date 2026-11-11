# CHOAM

**Commerce, with rules.** Agentic commerce infrastructure with deterministic authorization boundaries.

## Status

Initial repository foundation. See `TESTING.md` and `docs/architecture.md`.

## Local development

Backend: `cd backend && pip install -e '.[dev]' && alembic upgrade head && uvicorn app.main:app --reload`

Frontend: `cd frontend && npm install && npm run dev`

Python 3.11+, Node 20+ and PostgreSQL 15+ are expected. Copy `.env.example` to `backend/.env` and set `DATABASE_URL`.

CHOAM is a working name. Naming and trademark clearance is required before launch; this project is not affiliated with or endorsed by the Dune franchise.
