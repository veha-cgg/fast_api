from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from models.users import User
    from models.products import Product

class OrderStatus(str, Enum):   
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"
    refunded = "refunded"
    failed = "failed"

class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    total_amount: float = Field(default=0.0)
    status: OrderStatus = Field(default=OrderStatus.pending)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    user_id: int = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="orders")

    product_id: int = Field(foreign_key="products.id")
    product: "Product" = Relationship(back_populates="orders")

class OrderCreate(SQLModel):
    total_amount: float = Field(default=0.0)
    status: OrderStatus = Field(default=OrderStatus.pending)
    user_id: int = Field(foreign_key="user.id")
    product_id: int = Field(foreign_key="products.id")

class OrderUpdate(SQLModel):
    total_amount: Optional[float] = None
    status: Optional[OrderStatus] = None
    user_id: Optional[int] = None
    product_id: Optional[int] = None

class OrderResponse(SQLModel):
    id: int
    total_amount: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    user_id: int
    product_id: int

from models.users import User
from models.products import Product