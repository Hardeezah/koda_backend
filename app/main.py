from fastapi import FastAPI
from app.api.v1.endpoints import afcfta
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import health, profile, ledger, products, compliance, documents, communication_api, orchestration, auth

app = FastAPI(title="KodaTrade API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def root():
    return {"message": "Welcome to KodaTrade API"}
