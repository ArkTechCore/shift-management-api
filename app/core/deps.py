from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import SessionLocal
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)

# Only these paths are allowed when must_change_password = true
_PASSWORD_CHANGE_ALLOWLIST = {
    f"{settings.API_V1_STR}/auth/change-password",
    # login does NOT use get_current_user, so it's not required here
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _credentials_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    # Strict: must have token
    if not token:
        raise _credentials_exception()

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise _credentials_exception()
    except JWTError:
        raise _credentials_exception()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise _credentials_exception()

    # ✅ FORCE PASSWORD CHANGE GATE
    # If must_change_password is true, block all protected APIs except allowlist
    if bool(getattr(user, "must_change_password", False)):
        path = request.url.path
        if path not in _PASSWORD_CHANGE_ALLOWLIST:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Password change required.",
            )

    return user


def get_current_user_optional(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if not user_id:
            return None
    except JWTError:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    # Optional user should NOT be blocked here (only enforced on protected endpoints)
    return user


def require_role(*roles: str):
    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return user

    return _checker
