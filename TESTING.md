# Testing

Backend: from `backend/`, install `pip install -e '.[dev]'`, then run `pytest -q` and `ruff check app tests`.

Frontend: from `frontend/`, run `npm install`, `npm run lint`, `npm run typecheck`, and `npm run build`.

PostgreSQL migration and readiness success require a running PostgreSQL instance. CI executes the backend and frontend checks.
