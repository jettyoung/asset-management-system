from typing import Optional
from sqlmodel import SQLModel, Field

class ProductBase(SQLModel):
    name: str
    sku: str
    price: float
    current_stock: int = 0
    reorder_level: int = 0

class Product(ProductBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class ProductCreate(ProductBase):
    """Schema for creating a product (no id yet)."""
    pass

class ProductRead(ProductBase):
    """Schema for reading a product (includes id)."""
    id: int

from typing import Optional
from sqlmodel import SQLModel, Field

class CustomerBase(SQLModel):
    name: str
    email: str
    address: str | None = None  # optional

class Customer(CustomerBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class CustomerCreate(CustomerBase):
    """Schema for creating a customer (no id yet)."""
    pass

class CustomerRead(CustomerBase):
    """Schema for reading a customer (includes id)."""
    id: int