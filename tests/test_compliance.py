import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


class MockIntelligenceService:
    async def analyze_compliance(self, product_name, hs_code=None, direction="import", **kwargs):
        return {
            "status": "compliant",
            "summary": "Test summary",
            "risks": [{"level": "low", "reason": "Verified", "action_required": None}],
            "retrieval_used": False,
            "citations": [],
        }


@pytest.mark.asyncio
async def test_check_compliance():
    import app.api.v1.endpoints.compliance as compliance_mod
    from app.api.v1.deps import get_current_user

    original_service = compliance_mod.intelligence_service
    compliance_mod.intelligence_service = MockIntelligenceService()

    async def mock_auth(authorization=None):
        return "test_user"

    app.dependency_overrides[get_current_user] = mock_auth

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"product_name": "Ginger"}
        response = await ac.post("/api/v1/compliance/check", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "compliant"

    compliance_mod.intelligence_service = original_service
    app.dependency_overrides.clear()
