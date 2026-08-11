"""
Product management routes
"""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
import math

from db import engine
from models import Product, StockUpdate
from routes.async_utils import async_route

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
@async_route
def get_products(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(50, ge=1, le=500, description="Number of items per page (max 500)")
):
    """Get all products with pagination"""
    try:
        with engine.connect() as conn:
            # Get total count
            count_result = conn.execute(text("SELECT COUNT(*) FROM products"))
            total_items = count_result.fetchone()[0]
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = math.ceil(total_items / page_size)
            
            # Get paginated results
            result = conn.execute(text("""
                SELECT p.product_id, p.name, p.barcode, p.price, p.stock_quantity, 
                       p.low_stock_threshold, p.category_id, c.name as category, 
                       p.supplier_id, s.name as supplier, p.cost_price
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.category_id
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
                ORDER BY p.product_id
                LIMIT :limit OFFSET :offset
            """), {"limit": page_size, "offset": offset})
            rows = result.fetchall()
        
        products = [
            {
                "product_id": r[0],
                "name": r[1],
                "barcode": r[2],
                "price": float(r[3]) if r[3] else 0,
                "stock_quantity": r[4],
                "low_stock_threshold": r[5],
                "category_id": r[6],
                "category": r[7],
                "supplier_id": r[8],
                "supplier": r[9],
                "cost_price": float(r[10]) if r[10] else 0
            }
            for r in rows
        ]
        return {
            "products": products,
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


@router.get("/{product_id}")
@async_route
def get_product(product_id: int):
    """Get a single product by ID"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT p.product_id, p.name, p.barcode, p.price, p.stock_quantity, 
                       p.low_stock_threshold, p.category_id, c.name as category, 
                       p.supplier_id, s.name as supplier, p.cost_price
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.category_id
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
                WHERE p.product_id = :pid
            """), {"pid": product_id})
            row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product = {
            "product_id": row[0],
            "name": row[1],
            "barcode": row[2],
            "price": float(row[3]) if row[3] else 0,
            "stock_quantity": row[4],
            "low_stock_threshold": row[5],
            "category_id": row[6],
            "category": row[7],
            "supplier_id": row[8],
            "supplier": row[9],
            "cost_price": float(row[10]) if row[10] else 0
        }
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
@async_route
def add_product(product: Product):
    """Add a new product"""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT INTO products (name, barcode, price, stock_quantity, category_id, supplier_id, low_stock_threshold, cost_price)
                VALUES (:name, :barcode, :price, :stock, :category_id, :supplier_id, :threshold, :cost_price)
                RETURNING product_id
            """), {
                "name": product.name,
                "barcode": product.barcode,
                "price": product.price,
                "stock": product.stock_quantity,
                "category_id": product.category_id,
                "supplier_id": product.supplier_id,
                "threshold": product.low_stock_threshold,
                "cost_price": product.cost_price if product.cost_price is not None else product.price * 0.6
            })
            product_id = result.fetchone()[0]
            
        return {"message": "Product added successfully", "product_id": product_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{product_id}/stock")
@async_route
def update_stock(product_id: int, stock_update: StockUpdate):
    """Update product stock quantity"""
    try:
        with engine.begin() as conn:
            # Get old stock first
            old_result = conn.execute(text("SELECT name, stock_quantity FROM products WHERE product_id = :pid"), {"pid": product_id})
            old_data = old_result.fetchone()
            old_stock = old_data[1] if old_data else 0
            
            result = conn.execute(text("""
                UPDATE products 
                SET stock_quantity = stock_quantity + :qty
                WHERE product_id = :pid
                RETURNING name, stock_quantity
            """), {"qty": stock_update.quantity, "pid": product_id})
            
            updated = result.fetchone()
            if not updated:
                raise HTTPException(status_code=404, detail="Product not found")
            
        
        return {"message": f"Stock updated for {updated[0]}", "new_stock": updated[1]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))