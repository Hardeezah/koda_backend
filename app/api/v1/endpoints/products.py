from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.domain.models import ProductMetadata
from app.domain.repositories import ProductRepository
from app.api.v1.deps import get_product_repo

router = APIRouter()

@router.get("/", response_model=List[ProductMetadata])
async def list_products(repo: ProductRepository = Depends(get_product_repo)):
    return await repo.list_all()

@router.get("/{product_id}", response_model=ProductMetadata)
async def get_product(
    product_id: str,
    repo: ProductRepository = Depends(get_product_repo)
):
    product = await repo.get_by_id(product_id.lower())
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
