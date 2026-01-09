from fastapi import FastAPI, Request, HTTPException
from app.api.api_v1.api import api_router
from app.core.config import settings
from jose import jwt, JWTError
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Shift Management API", version="0.1.0")

# ---------------------------
# MUST CHANGE PASSWORD GUARD
# ---------------------------
ALLOWLIST_PATHS = {
    "/",
    "/health",
    f"{settings.API_V1_STR}/auth/login",
    f"{settings.API_V1_STR}/auth/change-password",
}


@app.middleware("http")
async def must_change_password_guard(request: Request, call_next):
    path = request.url.path

    # allow public + auth paths
    if path in ALLOWLIST_PATHS:
        return await call_next(request)

    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return await call_next(request)

    token = auth.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return await call_next(request)

    if payload.get("must_change_password") is True:
        raise HTTPException(
            status_code=403,
            detail="Password change required before accessing this resource.",
        )

    return await call_next(request)


# ---------------------------
# ROUTES
# ---------------------------
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"status": "ok", "service": "shift-management-api"}


@app.get("/health")
def health():
    return {"ok": True}



# ---------------------------
# CORS (required for web apps)
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:58442",
        "http://localhost:8080",
        "http://localhost:4200",
        "http://localhost",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        # add your domains later:
        # "https://yourdomain.com",
        # "https://www.yourdomain.com",
    ],
    allow_credentials=False,  # keep false for simple + reliable browser behavior
    allow_methods=["*"],
    allow_headers=["*"],
)
