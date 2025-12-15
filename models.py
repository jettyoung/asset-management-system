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
