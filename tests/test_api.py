import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_verify_unauthorized():
    response = client.post(
        "/api/cnas/verify",
        json={
            "Numéro de l'attestation": "25/1234567",
            "Numéro de l'employeur": "16/0001234"
        }
    )
    if response.status_code == 422:
        print(response.json())
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid API Key"

def test_verify_populate_by_name():
    # This should work because of model_config = {"populate_by_name": True}
    response = client.post(
        "/api/cnas/verify",
        headers={"x-internal-api-key": settings.INTERNAL_API_KEY},
        json={
            "attestation_number": "25/1234567",
            "employer_number": "16/0001234"
        }
    )
    # It might return 200 or something else depending on scraper mock, 
    # but it shouldn't be 422
    assert response.status_code != 422

def test_verify_invalid_input():
    response = client.post(
        "/api/cnas/verify",
        headers={"x-internal-api-key": settings.INTERNAL_API_KEY},
        json={"attestation_number": "invalid", "employer_number": "16/0001234"}
    )
    assert response.status_code == 422 # Pydantic validation error
