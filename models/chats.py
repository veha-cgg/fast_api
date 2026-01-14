from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import Optional, List
from typing import TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from models.users import User

class ChatType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"
    BROADCAST = "broadcast"

class Chat(SQLModel, table=True):
    __tablename__ = "chats"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    message: str
    message_type: ChatType = Field(default=ChatType.PRIVATE)
    sender_id: int = Field(foreign_key="user.id")
    receiver_id: Optional[int] = Field(default=None, foreign_key="user.id")  
    chat_room_id: Optional[int] = Field(default=None, foreign_key="chat_rooms.id")  
    parent_message_id: Optional[int] = Field(default=None, foreign_key="chats.id") 
    
    is_read: bool = Field(default=False)
    read_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    sender: "User" = Relationship(back_populates="chats", sa_relationship_kwargs={"foreign_keys": "Chat.sender_id"})
    receiver: Optional["User"] = Relationship(back_populates="received_chats", sa_relationship_kwargs={"foreign_keys": "Chat.receiver_id"})
    parent_message: Optional["Chat"] = Relationship(
        sa_relationship_kwargs={
            "remote_side": "Chat.id",
            "foreign_keys": "Chat.parent_message_id"
        }
    )
    user_chats: List["UserChat"] = Relationship(back_populates="chat")
    chat_room: Optional["ChatRoom"] = Relationship(back_populates="messages")


class UserChat(SQLModel, table=True):
    __tablename__ = "user_chats"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    chat_id: int = Field(foreign_key="chats.id")
    is_archived: bool = Field(default=False)
    is_starred: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    
    user: "User" = Relationship(back_populates="user_chats")
    chat: "Chat" = Relationship(back_populates="user_chats")


class ChatRoom(SQLModel, table=True):
    __tablename__ = "chat_rooms"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    is_private: bool = Field(default=False)
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    messages: List["Chat"] = Relationship(back_populates="chat_room")
    participants: List["ChatRoomParticipant"] = Relationship(back_populates="chat_room")
    created_by: "User" = Relationship()


class ChatRoomParticipant(SQLModel, table=True):
    __tablename__ = "chat_room_participants"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    chat_room_id: int = Field(foreign_key="chat_rooms.id")
    user_id: int = Field(foreign_key="user.id")
    role: str = Field(default="member")  
    joined_at: datetime = Field(default_factory=datetime.now)
    last_read_at: Optional[datetime] = None
    
    chat_room: "ChatRoom" = Relationship(back_populates="participants")
    user: "User" = Relationship()