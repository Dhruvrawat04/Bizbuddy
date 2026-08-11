from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from routes import (
    auth_router,
    products_router,
    categories_router,
    suppliers_router,
    sales_router,
    customers_router,
    employees_router,
    purchase_orders_router,
    dashboard_router,
    notifications_router,
    reports_router,
    exports_router,
    audit_logs_router,
)

app = FastAPI(title="SuperMarket Management API")

allowed_origins = [
    "http://localhost:5000",
    "http://localhost:3000",
    os.getenv("FRONTEND_URL", ""),
]
if not os.getenv("FRONTEND_URL"):
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(categories_router)
app.include_router(suppliers_router)
app.include_router(sales_router)
app.include_router(customers_router)
app.include_router(employees_router)
app.include_router(purchase_orders_router)
app.include_router(dashboard_router)
app.include_router(notifications_router)
app.include_router(reports_router)
app.include_router(exports_router)
app.include_router(audit_logs_router)


@app.get("/")
async def root():
    return {"message": "SuperMarket Management API", "version": "1.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
