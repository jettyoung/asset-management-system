from typing import List
from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import SQLModel, Session, create_engine, select
from models import (
    Product, ProductCreate, ProductRead,
    Customer, CustomerCreate, CustomerRead,
    Order, OrderItem, OrderCreate, OrderRead, OrderItemRead
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

# --------- Order endpoints ----------

@app.post("/orders", response_model=OrderRead)
def create_order(
    order_data: OrderCreate,
    session: Session = Depends(get_session),
):
    # 1) Confirm customer exists
    customer = session.get(Customer, order_data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if len(order_data.items) == 0:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    # 2) Validate stock for each item BEFORE modifying anything
    products_to_update = []  # list of (product, quantity)
    for item in order_data.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Item quantity must be > 0")

        product = session.get(Product, item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product not found: {item.product_id}")

        if product.current_stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for product {product.id} (have {product.current_stock}, need {item.quantity})"
            )

        products_to_update.append((product, item.quantity))

    # 3) Create the order
    order = Order(customer_id=order_data.customer_id, status="PENDING")
    session.add(order)
    session.commit()
    session.refresh(order)  # now order.id exists

    # 4) Create order items + decrement stock
    created_items: List[OrderItem] = []
    for product, qty in products_to_update:
        # decrement stock
        product.current_stock -= qty
        session.add(product)

        # create item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=qty,
            unit_price=product.price,
        )
        session.add(order_item)
        created_items.append(order_item)

    session.commit()

    # 5) Load items from DB for the response
    items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()

    return OrderRead(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status,
        created_at=order.created_at,
        items=[OrderItemRead(**item.model_dump()) for item in items],
    )


@app.get("/orders", response_model=List[OrderRead])
def list_orders(session: Session = Depends(get_session)):
    orders = session.exec(select(Order)).all()

    result: List[OrderRead] = []
    for o in orders:
        items = session.exec(select(OrderItem).where(OrderItem.order_id == o.id)).all()
        result.append(
            OrderRead(
                id=o.id,
                customer_id=o.customer_id,
                status=o.status,
                created_at=o.created_at,
                items=[OrderItemRead(**item.model_dump()) for item in items],
            )
        )
    return result


@app.get("/orders/{order_id}", response_model=OrderRead)
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()

    return OrderRead(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status,
        created_at=order.created_at,
        items=[OrderItemRead(**item.model_dump()) for item in items],
    )