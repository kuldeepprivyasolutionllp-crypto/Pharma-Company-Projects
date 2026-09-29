from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .auth import create_access_token, get_current_user, password_hash, verify_password
from .config import settings
from .db import ensure_database_and_schema, get_db
from .models import Equipment, Permission, Role, RolePermission, User
from .schemas import (LoginRequest, PermissionResponse, RoleCreateRequest, RoleResponse, RoleRightsRequest,
                      RoleUpdateRequest, SignupRequest, TokenResponse, UserAdminResponse, UserCreateRequest,
                      UserResponse, UserUpdateRequest, EquipmentCreateRequest, EquipmentResponse,
                      EquipmentUpdateRequest)

app = FastAPI(title="Amneal Authentication API", version="1.0.0")


@app.on_event("startup")
def startup():
    ensure_database_and_schema()


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email already exists")

    user = User(
        email=email,
        password_hash=password_hash.hash(payload.password),
        full_name=payload.full_name.strip(),
        role="operator",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return TokenResponse(
        access_token=create_access_token(user),
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            last_login=user.last_login,
        ),
    )


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect")

    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return TokenResponse(
        access_token=create_access_token(user),
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            last_login=user.last_login,
        ),
    )


@app.get("/auth/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in {"admin", "superuser"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return user


def require_permission(permission_name: str):
    def permission_dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if user.role == "superuser":
            return user
        permission = db.scalar(select(Permission).where(Permission.name == permission_name))
        if permission is None or db.scalar(select(RolePermission).where(RolePermission.role_id == select(Role.id).where(Role.name == user.role).scalar_subquery(), RolePermission.permission_id == permission.id)) is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission required: {permission_name}")
        return user
    return permission_dependency


def admin_user_response(user: User) -> UserAdminResponse:
    return UserAdminResponse(
        id=user.id, email=user.email, full_name=user.full_name, role=user.role,
        is_active=user.is_active, created_at=user.created_at, last_login=user.last_login,
    )


@app.get("/admin/users", response_model=list[UserAdminResponse])
def list_users(_: User = Depends(require_permission("users_read")), db: Session = Depends(get_db)):
    return [admin_user_response(user) for user in db.scalars(select(User).order_by(User.id)).all()]


@app.post("/admin/users", response_model=UserAdminResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreateRequest, _: User = Depends(require_permission("users_create")), db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email already exists")
    if db.scalar(select(Role).where(Role.name == payload.role.lower(), Role.is_active.is_(True))) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role does not exist")
    user = User(email=email, password_hash=password_hash.hash(payload.password), full_name=payload.full_name.strip(), role=payload.role.lower(), is_active=payload.is_active)
    db.add(user)
    db.commit()
    db.refresh(user)
    return admin_user_response(user)


@app.patch("/admin/users/{user_id}", response_model=UserAdminResponse)
def update_user(user_id: int, payload: UserUpdateRequest, _: User = Depends(require_permission("users_update")), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    values = payload.model_dump(exclude_unset=True)
    if "email" in values:
        values["email"] = str(values["email"]).lower()
        duplicate = db.scalar(select(User).where(User.email == values["email"], User.id != user_id))
        if duplicate is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email already exists")
    if "role" in values:
        values["role"] = values["role"].lower()
        if db.scalar(select(Role).where(Role.name == values["role"], Role.is_active.is_(True))) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role does not exist")
    if "password" in values:
        user.password_hash = password_hash.hash(values.pop("password"))
    for field, value in values.items():
        setattr(user, field, value.strip() if isinstance(value, str) and field == "full_name" else value)
    db.commit()
    db.refresh(user)
    return admin_user_response(user)


@app.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, current_user: User = Depends(require_permission("users_delete")), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account")
    db.delete(user)
    db.commit()


def role_response(role: Role, db: Session) -> RoleResponse:
    user_count = db.scalar(select(User).where(User.role == role.name).with_only_columns(User.id).count()) if False else len(db.scalars(select(User.id).where(User.role == role.name)).all())
    return RoleResponse(id=role.id, name=role.name, description=role.description, scope=role.scope, is_active=role.is_active, user_count=user_count)


@app.get("/admin/roles", response_model=list[RoleResponse])
def list_roles(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [role_response(role, db) for role in db.scalars(select(Role).order_by(Role.id)).all()]


@app.post("/admin/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreateRequest, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    name = payload.name.strip().lower()
    if db.scalar(select(Role).where(Role.name == name)) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exists")
    role = Role(name=name, description=payload.description.strip(), scope=payload.scope.strip())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role_response(role, db)


@app.patch("/admin/roles/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, payload: RoleUpdateRequest, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    values = payload.model_dump(exclude_unset=True)
    if "name" in values:
        values["name"] = values["name"].strip().lower()
        duplicate = db.scalar(select(Role).where(Role.name == values["name"], Role.id != role_id))
        if duplicate is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exists")
        db.query(User).filter(User.role == role.name).update({"role": values["name"]}, synchronize_session=False)
    for field, value in values.items():
        setattr(role, field, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(role)
    return role_response(role, db)


@app.delete("/admin/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if db.scalar(select(User).where(User.role == role.name)) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role is assigned to users")
    db.delete(role)
    db.commit()


@app.get("/admin/permissions", response_model=list[PermissionResponse])
def list_permissions(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [PermissionResponse(id=permission.id, name=permission.name, description=permission.description)
            for permission in db.scalars(select(Permission).order_by(Permission.id)).all()]


@app.get("/admin/roles/{role_id}/rights", response_model=list[PermissionResponse])
def get_role_rights(role_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.get(Role, role_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    assigned = set(db.scalars(select(RolePermission.permission_id).where(RolePermission.role_id == role_id)).all())
    return [PermissionResponse(id=permission.id, name=permission.name, description=permission.description, allowed=permission.id in assigned)
            for permission in db.scalars(select(Permission).order_by(Permission.id)).all()]


@app.put("/admin/roles/{role_id}/rights", response_model=list[PermissionResponse])
def update_role_rights(role_id: int, payload: RoleRightsRequest, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.get(Role, role_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    permission_ids = set(payload.permission_ids)
    known_ids = set(db.scalars(select(Permission.id).where(Permission.id.in_(permission_ids))).all()) if permission_ids else set()
    if known_ids != permission_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more permissions do not exist")
    db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    db.add_all([RolePermission(role_id=role_id, permission_id=permission_id) for permission_id in permission_ids])
    db.commit()
    return get_role_rights(role_id, _, db)


@app.get("/equipment", response_model=list[EquipmentResponse])
def list_equipment(_: User = Depends(require_permission("equipment_read")), db: Session = Depends(get_db)):
    return db.scalars(select(Equipment).order_by(Equipment.id)).all()


@app.post("/equipment", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
def create_equipment(payload: EquipmentCreateRequest, _: User = Depends(require_permission("equipment_create")), db: Session = Depends(get_db)):
    values = payload.model_dump()
    values = {key: value.strip() if isinstance(value, str) else value for key, value in values.items()}
    if db.scalar(select(Equipment).where(Equipment.asset_tag == values["asset_tag"])) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Asset tag already exists")
    equipment = Equipment(**values)
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


@app.patch("/equipment/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(equipment_id: int, payload: EquipmentUpdateRequest, _: User = Depends(require_permission("equipment_update")), db: Session = Depends(get_db)):
    equipment = db.get(Equipment, equipment_id)
    if equipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    values = payload.model_dump(exclude_unset=True)
    if "asset_tag" in values:
        values["asset_tag"] = values["asset_tag"].strip()
        duplicate = db.scalar(select(Equipment).where(Equipment.asset_tag == values["asset_tag"], Equipment.id != equipment_id))
        if duplicate is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Asset tag already exists")
    for field, value in values.items():
        setattr(equipment, field, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(equipment)
    return equipment


@app.delete("/equipment/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(equipment_id: int, _: User = Depends(require_permission("equipment_delete")), db: Session = Depends(get_db)):
    equipment = db.get(Equipment, equipment_id)
    if equipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    db.delete(equipment)
    db.commit()
