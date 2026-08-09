"""
Supplier management routes
"""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
import math

from db import engine
from models import Supplier

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("")
async def get_suppliers(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(50, ge=1, le=500, description="Number of items per page (max 500)")
):
    """Get all suppliers with pagination"""
    try:
        with engine.connect() as conn:
            # Get total count
            count_result = conn.execute(text("SELECT COUNT(*) FROM suppliers"))
            total_items = count_result.fetchone()[0]
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = math.ceil(total_items / page_size)
            
            result = conn.execute(text("""
                SELECT s.supplier_id, s.name, s.phone, s.email, s.address, s.reliability_score, 
                       s.last_delivery_date, s.category_id, c.name as category_name
                FROM suppliers s
                LEFT JOIN categories c ON s.category_id = c.category_id
                ORDER BY s.name
                LIMIT :limit OFFSET :offset
            """), {"limit": page_size, "offset": offset})
            rows = result.fetchall()
        
        suppliers = [
            {
                "supplier_id": r[0], "name": r[1], "phone": r[2], "email": r[3], 
                "address": r[4], "reliability_score": r[5], "last_delivery_date": r[6],
                "category_id": r[7], "category_name": r[8]
            }
            for r in rows
        ]
        return {
            "suppliers": suppliers,
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
async def add_supplier(supplier: Supplier):
    """Add a new supplier"""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT INTO suppliers (name, phone, email, address, category_id)
                VALUES (:name, :phone, :email, :address, :category_id)
                RETURNING supplier_id
            """), {
                "name": supplier.name,
                "phone": supplier.phone,
                "email": supplier.email,
                "address": supplier.address,
                "category_id": supplier.category_id
            })
            supplier_id = result.fetchone()[0]
        return {"message": "Supplier added successfully", "supplier_id": supplier_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{supplier_id}")
async def update_supplier(supplier_id: int, supplier: Supplier):
    """Update an existing supplier"""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                UPDATE suppliers 
                SET name = :name, phone = :phone, email = :email, address = :address, category_id = :category_id
                WHERE supplier_id = :sid
                RETURNING supplier_id
            """), {
                "name": supplier.name,
                "phone": supplier.phone,
                "email": supplier.email,
                "address": supplier.address,
                "category_id": supplier.category_id,
                "sid": supplier_id
            })
            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Supplier not found")
        return {"message": "Supplier updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{supplier_id}")
async def delete_supplier(supplier_id: int):
    """Delete a supplier"""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("DELETE FROM suppliers WHERE supplier_id = :sid RETURNING supplier_id"), {"sid": supplier_id})
            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Supplier not found")
        return {"message": "Supplier deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))