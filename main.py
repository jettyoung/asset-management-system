from typing import List
from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import SQLModel, Session, create_engine, select
from models import (
    Product, ProductCreate, ProductRead,
    Customer, CustomerCreate, CustomerRead
)

# --------- FastAPI app ----------
app = FastAPI(title="Inventory & Order System")

# --------- Database setup ----------

# SQLite database file name
sqlite_file_name = "inventory.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# Create the database engine
engine = create_engine(sqlite_url, echo=True)  # echo=True logs SQL to the console

def create_db_and_tables() -> None:
    """Create database tables based on SQLModel models."""
    SQLModel.metadata.create_all(engine)

# Run once at startup
@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()

# Dependency to get a session
def get_session():
    with Session(engine) as session:
        yield session

# --------- Health check endpoint ----------

@app.get("/health")
def health_check():
    return {"status": "ok"}

# --------- Product endpoints ----------

@app.post("/products", response_model=ProductRead)
def create_product(
    product: ProductCreate,
    session: Session = Depends(get_session),
):
    # Create a Product instance from the incoming data
    db_product = Product.from_orm(product)

    # Save to database
    session.add(db_product)
    session.commit()
    session.refresh(db_product)  # reload with generated id

    return db_product

@app.get("/products", response_model=List[ProductRead])
def list_products(
    session: Session = Depends(get_session),
):
    statement = select(Product)
    results = session.exec(statement).all()
    return results

@app.get("/products/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int,
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    product_data: ProductCreate,
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update fields
    product.name = product_data.name
    product.sku = product_data.sku
    product.price = product_data.price
    product.current_stock = product_data.current_stock
    product.reorder_level = product_data.reorder_level

    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    session.delete(product)
    session.commit()
    return {"detail": "Product deleted"}

# --------- Customer endpoints ----------

@app.post("/customers", response_model=CustomerRead)
def create_customer(
    customer: CustomerCreate,
    session: Session = Depends(get_session),
):
    db_customer = Customer.from_orm(customer)
    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    return db_customer


@app.get("/customers", response_model=List[CustomerRead])
def list_customers(
    session: Session = Depends(get_session),
):
    statement = select(Customer)
    results = session.exec(statement).all()
    return results


@app.get("/customers/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    session: Session = Depends(get_session),
):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.put("/customers/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    customer_data: CustomerCreate,
    session: Session = Depends(get_session),
):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer.name = customer_data.name
    customer.email = customer_data.email
    customer.address = customer_data.address

    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


@app.delete("/customers/{customer_id}")
def delete_customer(
    customer_id: int,
    session: Session = Depends(get_session),
):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    session.delete(customer)
    session.commit()
    return {"detail": "Customer deleted"}
