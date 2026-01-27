from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from models.categories import Category
    from models.images import Image
    from models.users import User
    from models.providers import Provider
    from models.orders import Order
    from models.orders import OrderResponse

class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    is_active: bool = Field(default=True)

    category_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    category: Optional["Category"] = Relationship(back_populates="products")

    provider_id: Optional[int] = Field(default=None, foreign_key="providers.id")
    provider: Optional["Provider"] = Relationship(back_populates="products")

    images: List["Image"] = Relationship(back_populates="product")
    orders: List["Order"] = Relationship(back_populates="product")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional["User"] = Relationship(back_populates="products")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProductCreate(SQLModel):
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    is_active: bool = True
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    provider_id: Optional[int] = Field(default=None, foreign_key="providers.id")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")

class ProductUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    provider_id: Optional[int] = Field(default=None, foreign_key="providers.id")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")

class ProductResponse(SQLModel):
    id: int
    name: str
    description: Optional[str]
    price: Optional[float]
    quantity: Optional[int]
    is_active: bool
    category_id: Optional[int]
    provider_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    user_id: Optional[int]
    orders: List["OrderResponse"] = []

from models.providers import Provider  
from models.categories import Category      
from models.images import Image       
from models.users import User
from models.orders import Order, OrderResponse       
