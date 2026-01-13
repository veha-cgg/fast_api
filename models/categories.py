from sqlmodel import Field, SQLModel
from datetime import datetime
from typing import Optional

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class CategoryCreate(SQLModel):
    name: str
    description: Optional[str] = None

class CategoryUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CategoryResponse(SQLModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime