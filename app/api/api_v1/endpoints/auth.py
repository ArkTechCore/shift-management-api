from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if (user.status or "").lower() != "active":
        raise HTTPException(status_code=403, detail="Account disabled. Contact admin.")

    if user.locked_until is not None:
        # You can implement locked_until check; keeping it simple for now
        pass

    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # Tenant active check (only for tenant-scoped users)
    if user.tenant_id is not None and (user.role or "").lower() != "developer":
        t = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        if not t or not t.is_active:
            raise HTTPException(status_code=403, detail="Tenant disabled. Contact support.")

    token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "email": user.email,
        }
    )

    # must_change_password is handled on frontend via your middleware/allowlist idea
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        must_change_password=bool(getattr(user, "must_change_password", False)),
    )
