import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

class MockIntelligenceService:
    async def analyze_compliance(self, product_name, hs_code=None):
        from app.domain.models import ComplianceReport, TradeStatus, ComplianceRisk
        return ComplianceReport(
            status=TradeStatus.COMPLIANT,
            risks=[ComplianceRisk(level="low", reason="Verified")],
            summary="Test summary"
        )

@pytest.mark.asyncio
async def test_check_compliance():
    import app.api.v1.endpoints.compliance as compliance_mod
    original_service = compliance_mod.intelligence_service
    compliance_mod.intelligence_service = MockIntelligenceService()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "profile_id": "test",
            "product_name": "Ginger",
            "quantity": 1,
            "value_usd": 1
        }
        response = await ac.post("/api/v1/compliance/check", json=payload)
    
    assert response.status_code == 200
    assert response.json()["status"] == "compliant"
    
    compliance_mod.intelligence_service = original_service
