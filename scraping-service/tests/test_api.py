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
        ,
        headers={"x-internal-api-key": "wrong-key"},
        json={
            : "25/1234567",
            : "16/0001234"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API Key"

def test_verify_populate_by_name():
    
    response = client.post(
        ,
        headers={"x-internal-api-key": settings.INTERNAL_API_KEY},
        json={
            : "25/1234567",
            : "16/0001234"
        }
    )
    
    
    assert response.status_code != 422

def test_verify_invalid_input():
    response = client.post(
        ,
        headers={"x-internal-api-key": settings.INTERNAL_API_KEY},
        json={"attestation_number": "invalid", "employer_number": "16/0001234"}
    )
    assert response.status_code == 422 
