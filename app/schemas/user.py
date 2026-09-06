import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    gender: str | None = None
    goal: str | None = None
    activity_level: str | None = None


class UserCreate(UserBase):
    """Signup request body — sirf ye fields client bhejega"""
    password: str


class UserRead(UserBase):
    """API response — DB se aane wala data, password kabhi nahi"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Profile fields user can edit"""
    full_name: str | None = None
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    gender: str | None = None
    goal: str | None = None
    activity_level: str | None = None