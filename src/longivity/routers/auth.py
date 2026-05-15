"""Auth router — register, login, me."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import CurrentUser, DB
from ..core.security import create_access_token, hash_password, verify_password
from ..db.database import get_db
from ..db.models import Clinic, ClinicUser

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str | None = None
    clinic_name: str = "My Clinic"


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    clinic_id: str
    email: str
    full_name: str | None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    clinic_id: str
    role: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: DB):
    """Create a new clinic + admin user."""
    # Check email uniqueness
    existing = await db.execute(select(ClinicUser).where(ClinicUser.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create clinic
    clinic = Clinic(name=body.clinic_name)
    db.add(clinic)
    await db.flush()  # get clinic.id

    # Create user
    user = ClinicUser(
        clinic_id=clinic.id,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role="admin",
    )
    db.add(user)
    await db.flush()

    token = create_access_token({"sub": user.id, "clinic_id": clinic.id})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        clinic_id=clinic.id,
        email=user.email,
        full_name=user.full_name,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: DB):
    result = await db.execute(select(ClinicUser).where(ClinicUser.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token({"sub": user.id, "clinic_id": user.clinic_id})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        clinic_id=user.clinic_id,
        email=user.email,
        full_name=user.full_name,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        clinic_id=current_user.clinic_id,
        role=current_user.role,
    )
