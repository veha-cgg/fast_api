from enum import Enum
from sqlmodel import Field, SQLModel, Relationship
from pydantic import EmailStr
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from models.chats import Chat, UserChat, ChatRoom
    from models.products import Product
    from models.providers import Provider
    from models.orders import Order

class UserRole(str, Enum):
    super_admin = "super_admin"
    admin = "admin"
    user = "user"
    moderator = "moderator"

class User(SQLModel, table=True):
    __tablename__ = "user"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: EmailStr = Field(unique=True, index=True)
    password: str 
    role: UserRole = Field(default=UserRole.user)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    is_online: bool = Field(default=False)
    last_seen: Optional[datetime] = None
    
    # Relationships
    chats: List["Chat"] = Relationship(back_populates="sender", sa_relationship_kwargs={"foreign_keys": "Chat.sender_id"})
    received_chats: List["Chat"] = Relationship(back_populates="receiver", sa_relationship_kwargs={"foreign_keys": "Chat.receiver_id"})
    user_chats: List["UserChat"] = Relationship(back_populates="user")
    notifications: List["UserNotification"] = Relationship(back_populates="user")
    products: List["Product"] = Relationship(back_populates="user")
    providers: List["Provider"] = Relationship(back_populates="user")
    orders: List["Order"] = Relationship(back_populates="user")
    
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
    message: str
    data: Optional[UserData] = None
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

class UserNotification(SQLModel, table=True):
    __tablename__ = "user_notifications"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    message: str
    notification_type: str = Field(default="info") 
    is_read: bool = Field(default=False)
    read_at: Optional[datetime] = None
    related_chat_id: Optional[int] = Field(default=None, foreign_key="chats.id")
    created_at: datetime = Field(default_factory=datetime.now)
    
    user: "User" = Relationship(back_populates="notifications")