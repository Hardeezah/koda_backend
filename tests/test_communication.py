import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.v1.deps import get_profile_repo, get_ledger_repo, get_current_user
from app.domain.models import Profile, TradeEntry
from app.infrastructure.ai.communication import DraftEmail


class MockProfileRepo:
    async def get_by_id(self, profile_id):
        return Profile(id=profile_id, email="test@test.com", business_name="Test Corp")


class MockLedgerRepo:
    async def get_by_profile(self, profile_id):
        return [TradeEntry(id="entry_123", profile_id=profile_id, product_name="Ginger", quantity=100, value_usd=1000)]


class MockCommunicationService:
    async def draft_broker_email(self, entry, profile):
        return DraftEmail(subject="Test Subject", body="Test Body")


@pytest.mark.asyncio
async def test_draft_communication():
    import app.api.v1.endpoints.communication_api as comm_mod

    original_service = comm_mod.communication_service
    comm_mod.communication_service = MockCommunicationService()

    async def mock_auth(authorization=None):
        return "test_user"

    app.dependency_overrides[get_profile_repo] = lambda: MockProfileRepo()
    app.dependency_overrides[get_ledger_repo] = lambda: MockLedgerRepo()
    app.dependency_overrides[get_current_user] = mock_auth

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/communication/draft?entry_id=entry_123")

    assert response.status_code == 200
    assert response.json()["subject"] == "Test Subject"
    assert response.json()["body"] == "Test Body"

    app.dependency_overrides.clear()
    comm_mod.communication_service = original_service
