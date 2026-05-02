import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

HEADERS = {"X-Internal-API-Key": "shared-secret-with-nestjs-backend"}


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_ok(self, client):
        r = await client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["service"] == "ai-service"
        assert len(body["agents_loaded"]) == 6

    @pytest.mark.asyncio
    async def test_metrics_ok(self, client):
        r = await client.get("/api/metrics")
        assert r.status_code == 200
        body = r.json()
        assert "confidence_threshold" in body


class TestAuthMiddleware:
    @pytest.mark.asyncio
    async def test_missing_key_returns_422(self, client):
        # No header at all → FastAPI will return 422 (missing required header)
        r = await client.post("/api/classify", json={
            "file_url": "http://example.com/doc.jpg"
        })
        assert r.status_code in (401, 422)

    @pytest.mark.asyncio
    async def test_wrong_key_returns_401(self, client):
        r = await client.post(
            "/api/classify",
            json={"file_url": "http://example.com/doc.jpg"},
            headers={"X-Internal-API-Key": "wrong-key"},
        )
        assert r.status_code == 401


class TestConsistencyEndpoint:
    @pytest.mark.asyncio
    async def test_consistency_identical_names(self, client):
        r = await client.post(
            "/api/consistency",
            json={
                "documents": {
                    "national_id": {"name": {"value": "Ahmed Benali", "confidence": 0.9}},
                    "affiliation": {"name": {"value": "Ahmed Benali", "confidence": 0.9}},
                }
            },
            headers=HEADERS,
        )
        assert r.status_code == 200
        body = r.json()
        assert "consistency_score" in body
        assert body["consistency_score"] > 50

    @pytest.mark.asyncio
    async def test_consistency_empty_documents(self, client):
        r = await client.post(
            "/api/consistency",
            json={"documents": {}},
            headers=HEADERS,
        )
        assert r.status_code == 200


class TestScoreEndpoint:
    @pytest.mark.asyncio
    async def test_score_no_kyc(self, client):
        r = await client.post(
            "/api/score",
            json={
                "documents_submitted": ["affiliation_attestation"],
                "required_docs": [],
            },
            headers=HEADERS,
        )
        assert r.status_code == 200
        body = r.json()
        assert "score" in body
        assert "decision" in body

    @pytest.mark.asyncio
    async def test_score_with_full_input(self, client):
        r = await client.post(
            "/api/score",
            json={
                "kyc_result": {"passed": True, "liveness_score": 0.95},
                "cnas_result": {"valid": True},
                "documents_submitted": ["affiliation_attestation", "national_id"],
                "required_docs": ["affiliation_attestation"],
                "authenticity_results": {
                    "authenticity_score": 88.0,
                    "is_suspicious": False,
                    "checks": [],
                },
                "consistency_result": {
                    "consistency_score": 92.0,
                    "flags": [],
                    "checks": [],
                },
            },
            headers=HEADERS,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["score"] > 60
        assert body["decision"] in ("approved", "review")
