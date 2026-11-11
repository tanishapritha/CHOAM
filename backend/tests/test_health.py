from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_hides_database_error():
    async def unavailable_db():
        yield None

    app.dependency_overrides[get_db] = unavailable_db
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/v1/ready")
        assert response.status_code == 503
        assert response.json() == {"detail": "Database unavailable"}
    finally:
        app.dependency_overrides.clear()


def test_missing_route_is_404():
    with TestClient(app) as client:
        response = client.get("/missing")
    assert response.status_code == 404
