from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import ForeignKey
from datetime import datetime
from typing import Optional, List, Union
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.categories import Category
    from models.products import Product

class Image(SQLModel, table=True):
    __tablename__ = "images"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    category_id: Optional[int] = Field(default=None, sa_column=Column(ForeignKey("categories.id"), nullable=True))
    category: Optional["Category"] = Relationship(back_populates="images")
    
    product_id: Optional[int] = Field(default=None, sa_column=Column(ForeignKey("products.id"), nullable=True))
    product: Optional["Product"] = Relationship(back_populates="images")

class ImageData(SQLModel):
    """Image data model for use in responses (without wrapper)"""
    id: int
    url: str
    category_id: Optional[int] = None
    product_id: Optional[int] = None
    
    created_at: datetime
    updated_at: datetime

class ImageResponse(SQLModel):
    message: str
    data: Optional[Union[Image, List[Image]]] = None

class ImageListResponse(SQLModel):
    message: str
    data: List[Image] = []

class ImageCreate(SQLModel):
    url: str
    category_id: int | None = None
    product_id: int | None = None

class ImageUpdate(SQLModel):
    url: Optional[str] = None
    category_id: Optional[int] = None
    product_id: Optional[int] = None