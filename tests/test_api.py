from fastapi.testclient import TestClient
from ..app.main import app

client = TestClient(app)

def test_new_game():
    response = client.post("/api/v1/new-game", json={"difficulty": 5})
    assert response.status_code == 200
    assert "columns" in response.json()

def test_get_game_state():
    response = client.get("/api/v1/game-state")
    assert response.status_code == 200
    assert "columns" in response.json()