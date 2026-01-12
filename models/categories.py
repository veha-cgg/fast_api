from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

from datetime import datetime

class Category(BaseModel):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(default=None, unique=True)
    description: str = Field(default=None)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())

class CategoryCreate(BaseModel):
    name: str = Field(default=None, unique=True)
    description: str = Field(default=None)



class CategoryUpdate(BaseModel):
    name: str = Field(default=None, unique=True)
    description: str = Field(default=None)

class CategoryDelete(BaseModel):
    id: int = Field(default=None, primary_key=True)