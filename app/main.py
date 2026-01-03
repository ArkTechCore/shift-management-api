from fastapi import FastAPI
from app.api.api_v1.api import api_router

app = FastAPI(title="Shift Management API", version="0.1.0")

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"status": "ok", "service": "shift-management-api"}

@app.get("/health")
def health():
    return {"ok": True}
