from enum import Enum
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    moderator = "moderator"

class User(BaseModel):
    id: int = Field(default=None, primary_key=True)
    name: str
    email: EmailStr = Field(default=None, unique=True)
    password: str = Field(default=None)
    role: UserRole = Field(default=UserRole.user)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())

class UserCreate(BaseModel):
    name: str
    email: EmailStr = Field(default=None, unique=True)
    password: str = Field(default=None)
    role: UserRole = Field(default=UserRole.user)

class UserUpdate(BaseModel):
    name: str
    email: EmailStr = Field(default=None, unique=True)
    password: str = Field(default=None)
    c_password: str = Field(default=None)
    role: UserRole = Field(default=UserRole.user)

class UserDelete(BaseModel):
    id: int = Field(default=None, primary_key=True)