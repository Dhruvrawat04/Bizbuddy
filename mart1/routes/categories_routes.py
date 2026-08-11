"""
Category management routes
"""
from fastapi import APIRouter, HTTPException, Query, Request, Header
from sqlalchemy import text
import math
from typing import Optional

from db import engine
from models import Category
from routes.async_utils import async_route
from routes.audit_helper import model_to_dict, resolve_actor, write_audit

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
@async_route
def get_categories(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(100, ge=1, le=500, description="Number of items per page (max 500)")
):
    """Get all categories with pagination"""
    try:
        with engine.connect() as conn:
            # Get total count
            count_result = conn.execute(text("SELECT COUNT(*) FROM categories"))
            total_items = count_result.fetchone()[0]
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = math.ceil(total_items / page_size)
            
            result = conn.execute(text("""
                SELECT category_id, name, description 
                FROM categories 
                ORDER BY name
                LIMIT :limit OFFSET :offset
            """), {"limit": page_size, "offset": offset})
            rows = result.fetchall()
        
        categories = [
            {"category_id": r[0], "name": r[1], "description": r[2]}
            for r in rows
        ]
        return {
            "categories": categories,
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
def add_category(
    category: Category,
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Add a new category"""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT INTO categories (name, description)
                VALUES (:name, :description)
                RETURNING category_id
            """), {
                "name": category.name,
                "description": category.description
            })
            category_id = result.fetchone()[0]
        write_audit(
            action="INSERT",
            table_name="categories",
            record_id=category_id,
            new_values=model_to_dict(category),
            actor=resolve_actor(authorization),
            request=request,
        )
        return {"message": "Category added successfully", "category_id": category_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{category_id}")
@async_route
def update_category(
    category_id: int,
    category: Category,
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Update an existing category"""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                UPDATE categories 
                SET name = :name, description = :description
                WHERE category_id = :cid
                RETURNING category_id
            """), {
                "name": category.name,
                "description": category.description,
                "cid": category_id
            })
            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Category not found")
        write_audit(
            action="UPDATE",
            table_name="categories",
            record_id=category_id,
            new_values=model_to_dict(category),
            actor=resolve_actor(authorization),
            request=request,
        )
        return {"message": "Category updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{category_id}")
@async_route
def delete_category(
    category_id: int,
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Delete a category"""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("DELETE FROM categories WHERE category_id = :cid RETURNING category_id"), {"cid": category_id})
            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Category not found")
        write_audit(
            action="DELETE",
            table_name="categories",
            record_id=category_id,
            actor=resolve_actor(authorization),
            request=request,
        )
        return {"message": "Category deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))