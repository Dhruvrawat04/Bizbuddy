"""
Customer management routes
"""
from fastapi import APIRouter, HTTPException, Query, Request, Header
from sqlalchemy import text
import math
from typing import Optional

from db import engine
from models import Customer
from routes.async_utils import async_route
from routes.audit_helper import model_to_dict, resolve_actor, write_audit

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("")
@async_route
def get_customers(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(50, ge=1, le=500, description="Number of items per page (max 500)")
):
    """Get all customers with pagination"""
    try:
        with engine.connect() as conn:
            # Get total count
            count_result = conn.execute(text("SELECT COUNT(*) FROM customers"))
            total_items = count_result.fetchone()[0]
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = math.ceil(total_items / page_size)
            
            result = conn.execute(text("""
                SELECT customer_id, name, phone, email, gender, 
                       loyalty_points, total_spent, address, created_at 
                FROM customers 
                ORDER BY name
                LIMIT :limit OFFSET :offset
            """), {"limit": page_size, "offset": offset})
            rows = result.fetchall()
        
        customers = [
            {
                "customer_id": r[0], 
                "name": r[1], 
                "phone": r[2], 
                "email": r[3],
                "gender": r[4],
                "loyalty_points": r[5] or 0,
                "total_spent": float(r[6]) if r[6] else 0.0,
                "address": r[7],
                "created_at": r[8].isoformat() if r[8] else None
            }
            for r in rows
        ]
        return {
            "customers": customers,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
@async_route
def add_customer(
    customer: Customer,
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Add a new customer"""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT INTO customers (name, phone, email, gender)
                VALUES (:name, :phone, :email, :gender)
                RETURNING customer_id
            """), {
                "name": customer.name,
                "phone": customer.phone,
                "email": customer.email,
                "gender": customer.gender
            })
            customer_id = result.fetchone()[0]

        write_audit(
            action="INSERT",
            table_name="customers",
            record_id=customer_id,
            new_values=model_to_dict(customer),
            actor=resolve_actor(authorization),
            request=request,
        )
            
        return {"message": "Customer added successfully", "customer_id": customer_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))