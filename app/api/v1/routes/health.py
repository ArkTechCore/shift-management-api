from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    return {
        "ok": True,
        "service": settings.APP_NAME,
        "env": settings.ENV,
    }


@router.get("/")
def root():
    return {"status": "ok", "service": "shift-management-api"}
