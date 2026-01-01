from fastapi import FastAPI
from app.api.v1.router import api_router

app = FastAPI(title="Shift Management API", version="0.1.0")

@app.get("/")
def root():
    return {"status": "ok", "service": "shift-management-api"}

app.include_router(api_router, prefix="/api/v1")
