from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    must_change_password: bool = False
    tenant_id: Optional[str] = None
    email: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str