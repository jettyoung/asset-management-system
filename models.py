from datetime import datetime
from typing import Optional, List
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
    address: str | None = None

class Customer(CustomerBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class CustomerCreate(CustomerBase):
    """Schema for creating a customer (no id yet)."""
    pass

class CustomerRead(CustomerBase):
    """Schema for reading a customer (includes id)."""
    id: int

# ---------- Order + OrderItem ----------

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int
    status: str = "PENDING"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int
    product_id: int
    quantity: int
    unit_price: float


# ---------- Schemas for creating an order ----------

class OrderItemCreate(SQLModel):
    product_id: int
    quantity: int


class OrderCreate(SQLModel):
    customer_id: int
    items: List[OrderItemCreate]


# ---------- Schemas for reading an order ----------

class OrderItemRead(SQLModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float


class OrderRead(SQLModel):
    id: int
    customer_id: int
    status: str
    created_at: datetime
    items: List[OrderItemRead]
