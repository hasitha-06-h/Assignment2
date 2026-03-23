from fastapi import FastAPI, Query   
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI()  
# ------------------ SAMPLE DATA ------------------
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

# ------------------ Q1: FILTER PRODUCTS ------------------
@app.get("/products/filter")
def filter_products(
    min_price: int = Query(None),
    max_price: int = Query(None),
    category: str = Query(None)
):
    result = products

    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]

    if max_price:
        result = [p for p in result if p["price"] <= max_price]

    if min_price:
        result = [p for p in result if p["price"] >= min_price]

    
    result = [p for p in result if p["in_stock"]]

    return result


# ------------------ Q2: PRODUCT PRICE ------------------
@app.get("/products/{product_id}/price")
def get_price(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return {"name": p["name"], "price": p["price"]}
    return {"error": "Product not found"}


# ------------------ Q3: FEEDBACK ------------------
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

feedback = []

@app.post("/feedback")
def add_feedback(data: CustomerFeedback):
    feedback.append(data.dict())
    return {
        "message": "Feedback submitted successfully",
        "feedback": data,
        "total_feedback": len(feedback)
    }


# ------------------ Q4: PRODUCT SUMMARY ------------------
@app.get("/products/summary")
def summary():
    total = len(products)
    in_stock = len([p for p in products if p["in_stock"]])
    out_stock = total - in_stock

    most_exp = max(products, key=lambda x: x["price"])
    cheapest = min(products, key=lambda x: x["price"])

    categories = list(set([p["category"] for p in products]))

    return {
        "total_products": total,
        "in_stock_count": in_stock,
        "out_of_stock_count": out_stock,
        "most_expensive": {"name": most_exp["name"], "price": most_exp["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": categories
    }


# ------------------ Q5: BULK ORDER ------------------
class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem]

@app.post("/orders/bulk")
def bulk_order(order: BulkOrder):
    confirmed = []
    failed = []
    total = 0

    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)

        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
            continue

        if not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})
            continue

        subtotal = product["price"] * item.quantity
        total += subtotal

        confirmed.append({
            "product": product["name"],
            "qty": item.quantity,
            "subtotal": subtotal
        })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": total
    }

orders = []
order_counter = 1

@app.post("/orders")
def place_order(product_id: int, quantity: int):
    global order_counter

    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        return {"error": "Product not found"}

    order = {
        "order_id": order_counter,
        "product": product["name"],
        "quantity": quantity,
        "status": "pending"  
    }

    orders.append(order)
    order_counter += 1

    return {"message": "Order placed", "order": order}

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}
    return {"error": "Order not found"}

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {"message": "Order confirmed", "order": order}
    return {"error": "Order not found"}
