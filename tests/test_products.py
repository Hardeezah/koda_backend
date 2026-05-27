import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.v1.deps import get_product_repo
from app.domain.models import ProductMetadata

class MockProductRepo:
    async def list_all(self):
        return [
            ProductMetadata(id="ginger", name="Ginger", hs_code="0910.11", category="Spices")
        ]
    async def get_by_id(self, product_id):
        if product_id == "ginger":
            return ProductMetadata(id="ginger", name="Ginger", hs_code="0910.11", category="Spices")
        return None

@pytest.mark.asyncio
async def test_list_products():
    app.dependency_overrides[get_product_repo] = lambda: MockProductRepo()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/products/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == "ginger"
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_product_success():
    app.dependency_overrides[get_product_repo] = lambda: MockProductRepo()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/products/ginger")
    assert response.status_code == 200
    assert response.json()["id"] == "ginger"
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_product_not_found():
    app.dependency_overrides[get_product_repo] = lambda: MockProductRepo()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/products/unknown")
    assert response.status_code == 404
    app.dependency_overrides.clear()
