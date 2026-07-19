import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.main import app, Base, engine


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_eventos_seed_and_detail():
    client = TestClient(app)

    response = client.get("/eventos")
    assert response.status_code == 200
    eventos = response.json()
    assert len(eventos) >= 6

    event_id = eventos[0]["id"]
    detail_response = client.get(f"/eventos/{event_id}")
    assert detail_response.status_code == 200
    payload = detail_response.json()
    assert payload["id"] == event_id
