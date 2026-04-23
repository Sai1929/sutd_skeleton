import uuid

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    student_id: str
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    student_id: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserOut(BaseModel):
    id: uuid.UUID
    student_id: str
    email: str
    role: str
    full_name: str | None
    is_active: bool

    model_config = {"from_attributes": True}
