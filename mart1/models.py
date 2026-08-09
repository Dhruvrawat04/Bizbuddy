from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    employee_id: int
    name: str
    role: str
    message: str


class TokenData(BaseModel):
    employee_id: Optional[int] = None
    role: Optional[str] = None


class Product(BaseModel):
    name: str
    barcode: Optional[str] = None
    price: float
    stock_quantity: int
    category_id: int
    supplier_id: int
    low_stock_threshold: int = 10
    cost_price: Optional[float] = None


class SaleItem(BaseModel):
    product_id: int
    quantity: int


class Sale(BaseModel):
    items: List[SaleItem]
    payment_method: str
    customer_id: Optional[int] = None
    employee_id: int
    discount_percentage: Optional[float] = 0.0
    customer_rating: Optional[float] = None
    feedback: Optional[str] = None


class Customer(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    loyalty_points: Optional[int] = None
    total_spent: Optional[float] = None
    address: Optional[str] = None


class Employee(BaseModel):
    name: str
    role: str
    username: str
    password: str


class StockUpdate(BaseModel):
    product_id: int
    quantity: int


class Category(BaseModel):
    name: str
    description: Optional[str] = None


class Supplier(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    category_id: Optional[int] = None


class PurchaseOrderItem(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class PurchaseOrder(BaseModel):
    supplier_id: int
    items: List[Dict[str, Any]]
    status: str = "PENDING"


class NotificationUpdate(BaseModel):
    status: str


class AuditLogsRequest(BaseModel):
    user_role: str