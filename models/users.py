from enum import Enum
from sqlmodel import Field, SQLModel
from pydantic import EmailStr
from datetime import datetime
from typing import Optional

class UserRole(str, Enum):
    super_admin = "super_admin"
    admin = "admin"
    user = "user"
    moderator = "moderator"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: EmailStr = Field(unique=True, index=True)
    password: str 
    role: UserRole = Field(default=UserRole.user)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class UserCreate(SQLModel):
    name: str
    email: EmailStr
    password: str
    is_active: bool = Field(default=True)
    role: UserRole = Field(default=UserRole.user)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class UserUpdate(SQLModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None    

class UserData(SQLModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

class TokenData(SQLModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class UserResponse(SQLModel):
    data: UserData
    token: TokenData

class UpdateUserPassword(SQLModel):
    current_password: str
    new_password: str
    confirm_new_password: str

class LoginRequest(SQLModel):
    email: EmailStr
    password: str

class UserLogin(SQLModel):
    email: EmailStr
    password: str
    is_active: bool
   
class Token(SQLModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class TokenPayload(SQLModel):
    email: str | None = None
    role: str | None = None

class RefreshTokenRequest(SQLModel):
    refresh_token: str