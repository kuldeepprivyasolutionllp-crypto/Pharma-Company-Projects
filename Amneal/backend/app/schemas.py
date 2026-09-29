from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str = "operator"
    last_login: datetime | None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserAdminResponse(UserResponse):
    is_active: bool
    created_at: datetime


class UserCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="operator", min_length=2, max_length=50)
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: str | None = Field(default=None, min_length=2, max_length=50)
    is_active: bool | None = None


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str
    scope: str
    is_active: bool
    user_count: int = 0


class RoleCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    description: str = Field(min_length=2, max_length=255)
    scope: str = Field(min_length=2, max_length=100)


class RoleUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = Field(default=None, min_length=2, max_length=255)
    scope: str | None = Field(default=None, min_length=2, max_length=100)
    is_active: bool | None = None


class PermissionResponse(BaseModel):
    id: int
    name: str
    description: str
    allowed: bool = False


class RoleRightsRequest(BaseModel):
    permission_ids: list[int] = Field(default_factory=list)


class EquipmentResponse(BaseModel):
    id: int
    asset_tag: str
    name: str
    category: str
    location: str
    status: str
    calibration_due: str


class EquipmentCreateRequest(BaseModel):
    asset_tag: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=150)
    category: str = Field(min_length=2, max_length=80)
    location: str = Field(min_length=2, max_length=100)
    status: str = Field(default="Operational", max_length=30)
    calibration_due: str = Field(min_length=8, max_length=20)


class EquipmentUpdateRequest(BaseModel):
    asset_tag: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    category: str | None = Field(default=None, min_length=2, max_length=80)
    location: str | None = Field(default=None, min_length=2, max_length=100)
    status: str | None = Field(default=None, max_length=30)
    calibration_due: str | None = Field(default=None, min_length=8, max_length=20)
