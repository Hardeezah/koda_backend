import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.api.v1.endpoints import (
    health,
    auth,
    profile,
    ledger,
    products,
    compliance,
    documents,
    communication_api,
    orchestration,
    afcfta,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="KodaTrade API", version="0.1.0")

ALLOWED_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:8081,http://localhost:3000,http://localhost:19006",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["profile"])
app.include_router(ledger.router, prefix="/api/v1/ledger", tags=["ledger"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["compliance"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(communication_api.router, prefix="/api/v1/communication", tags=["communication"])
app.include_router(orchestration.router, prefix="/api/v1/orchestration", tags=["orchestration"])
app.include_router(afcfta.router, prefix="/api/v1/afcfta", tags=["afcfta"])


@app.get("/")
async def root():
    return {"message": "Welcome to KodaTrade API"}
