import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.v1.deps import get_product_repo, get_ledger_repo, get_profile_repo
from app.domain.models import ProductMetadata, ComplianceReport, TradeStatus, ComplianceRisk

class MockProductRepo:
    async def get_by_name(self, name):
        if name == "Ginger":
            return ProductMetadata(id="1", name="Ginger", hs_code="0910.11", category="Agriculture", common_unit="kg")
        return None

class MockLedgerRepo:
    async def create(self, entry):
        return entry

class MockProfileRepo:
    async def get_by_id(self, profile_id):
        pass

class MockIntelligenceService:
    async def analyze_compliance(self, product_name, hs_code=None):
        return ComplianceReport(
            status=TradeStatus.COMPLIANT,
            risks=[ComplianceRisk(level="low", reason="Verified")],
            summary="Orchestrated check"
        )

@pytest.mark.asyncio
async def test_orchestration_process():
    import app.api.v1.endpoints.orchestration as orch_mod
    original_service = orch_mod.intelligence_service
    orch_mod.intelligence_service = MockIntelligenceService()

    app.dependency_overrides[get_product_repo] = lambda: MockProductRepo()
    app.dependency_overrides[get_ledger_repo] = lambda: MockLedgerRepo()
    app.dependency_overrides[get_profile_repo] = lambda: MockProfileRepo()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "product_name": "Ginger",
            "quantity": 100,
            "value_usd": 1000
        }
        response = await ac.post("/api/v1/orchestration/process", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "entry_id" in data
    assert data["product_metadata"]["hs_code"] == "0910.11"
    assert data["compliance_report"]["status"] == "compliant"
    
    app.dependency_overrides.clear()
    orch_mod.intelligence_service = original_service
