from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from models.users import User
    from models.products import Product, ProductResponse

class Provider(SQLModel, table=True):
    __tablename__ = "providers"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional["User"] = Relationship(back_populates="providers")

    products: List["Product"] = Relationship(back_populates="provider")

class ProviderCreate(SQLModel):
    name: str
    description: Optional[str] = None
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")

class ProviderUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")

class ProviderResponse(SQLModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    user_id: Optional[int]
    products: List["ProductResponse"] = []

from models.products import Product, ProductResponse  
from models.users import User

