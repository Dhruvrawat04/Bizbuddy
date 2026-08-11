"""
Sales management routes
"""
from fastapi import APIRouter, HTTPException, Query, Request, Header
from sqlalchemy import text
import math
from typing import Optional

from db import engine
from models import Sale
from routes.async_utils import async_route
from routes.audit_helper import resolve_actor, write_audit

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.post("")
@async_route
def create_sale(
    sale: Sale,
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Create a new sale transaction"""
    try:
        total = 0.0
        cart = []
        
        with engine.connect() as conn:
            # OPTIMIZED: Fetch ALL products at once instead of 1 per item (N+1 elimination)
            product_ids = [item.product_id for item in sale.items]
            products_query = f"""
                SELECT product_id, name, price, stock_quantity
                FROM products
                WHERE product_id = ANY(ARRAY[{','.join(map(str, product_ids))}])
            """
            products_result = conn.execute(text(products_query))
            products_map = {r[0]: {'name': r[1], 'price': r[2], 'stock': r[3]} for r in products_result}
            
            # Validate stock for all items
            for item in sale.items:
                if item.product_id not in products_map:
                    raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
                
                product_data = products_map[item.product_id]
                if product_data['stock'] < item.quantity:
                    raise HTTPException(status_code=400, detail=f"Only {product_data['stock']} units in stock for {product_data['name']}")
                
                item_total = float(product_data['price']) * item.quantity
                cart.append({
                    'product_id': item.product_id,
                    'quantity': item.quantity,
                    'price': float(product_data['price']),
                    'subtotal': item_total
                })
                total += item_total
        
        # Apply discount if provided
        discount_amount = 0
        if sale.discount_percentage and sale.discount_percentage > 0:
            discount_amount = total * (sale.discount_percentage / 100)
            total = total - discount_amount
        
        with engine.begin() as conn:
            # OPTIMIZED: Validate customer AND get employee info in ONE query (was 2 separate queries)
            validation_query = """
                SELECT 
                    CASE WHEN c.customer_id IS NOT NULL OR :cid IS NULL THEN 1 ELSE 0 END as customer_valid,
                    e.username,
                    e.role
                FROM employees e
                LEFT JOIN customers c ON c.customer_id = :cid
                WHERE e.employee_id = :eid
            """
            validation = conn.execute(text(validation_query), {"cid": sale.customer_id, "eid": sale.employee_id}).fetchone()
            
            if not validation:
                raise HTTPException(status_code=404, detail="Employee not found")
            
            if sale.customer_id and validation[0] == 0:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            emp_username = validation[1] if validation[1] else "unknown"
            emp_role = validation[2] if validation[2] else "unknown"
            
            result = conn.execute(text("""
                INSERT INTO sales (total_amount, payment_method, customer_id, employee_id, 
                                   discount_percentage, customer_rating, feedback, sale_time)
                VALUES (:total, :pm, :cid, :eid, :discount, :rating, :feedback, CURRENT_TIMESTAMP)
                RETURNING sale_id
            """), {
                "total": round(total, 2),
                "pm": sale.payment_method,
                "cid": sale.customer_id,
                "eid": sale.employee_id,
                "discount": sale.discount_percentage,
                "rating": sale.customer_rating,
                "feedback": sale.feedback
            })
            sale_id = result.fetchone()[0]
            
            # OPTIMIZED: Bulk insert all sale items (still using loop but in single transaction)
            for item in cart:
                conn.execute(text("""
                    INSERT INTO sale_items (sale_id, product_id, quantity, unit_price)
                    VALUES (:sale_id, :pid, :qty, :price)
                """), {
                    "sale_id": sale_id,
                    "pid": item['product_id'],
                    "qty": item['quantity'],
                    "price": item['price']
                })
            
            # OPTIMIZED: Bulk update stock using CASE instead of loop (N queries -> 1 query)
            case_statement = " ".join([
                f"WHEN {item['product_id']} THEN stock_quantity - {item['quantity']}"
                for item in cart
            ])
            update_query = f"""
                UPDATE products
                SET stock_quantity = CASE product_id
                    {case_statement}
                    ELSE stock_quantity
                END
                WHERE product_id = ANY(ARRAY[{','.join(map(str, [item['product_id'] for item in cart]))}])
            """
            conn.execute(text(update_query))
            
        actor = resolve_actor(authorization, employee_id=sale.employee_id, username=emp_username, role=emp_role)
        write_audit(
            action="INSERT",
            table_name="sales",
            record_id=sale_id,
            new_values={
                "sale_id": sale_id,
                "total_amount": round(total, 2),
                "payment_method": sale.payment_method,
                "customer_id": sale.customer_id,
                "employee_id": sale.employee_id,
                "item_count": len(cart),
                "items": cart,
            },
            actor=actor,
            request=request,
        )
        
        return {"message": "Sale completed successfully", "sale_id": sale_id, "total": total}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
@async_route
def get_sales(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(50, ge=1, le=500, description="Number of items per page (max 500)")
):
    """Get all sales with pagination"""
    try:
        with engine.connect() as conn:
            # Get total count
            count_result = conn.execute(text("SELECT COUNT(*) FROM sales"))
            total_items = count_result.fetchone()[0]
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = math.ceil(total_items / page_size)
            
            result = conn.execute(text("""
                SELECT s.sale_id, s.sale_time, s.total_amount, s.payment_method, 
                       c.name as customer, e.name as employee,
                       s.discount_percentage, s.customer_rating, s.feedback
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.customer_id
                LEFT JOIN employees e ON s.employee_id = e.employee_id
                ORDER BY s.sale_time DESC
                LIMIT :limit OFFSET :offset
            """), {"limit": page_size, "offset": offset})
            rows = result.fetchall()
        
        sales = [
            {
                "sale_id": r[0],
                "sale_time": str(r[1]),
                "total_amount": float(r[2]),
                "payment_method": r[3],
                "customer": r[4],
                "employee": r[5],
                "discount_percentage": float(r[6]) if r[6] else 0.0,
                "customer_rating": float(r[7]) if r[7] else None,
                "feedback": r[8]
            }
            for r in rows
        ]
        return {
            "sales": sales,
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


@router.get("/{sale_id}")
@async_route
def get_sale_details(sale_id: int):
    """Get details of a specific sale"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT si.product_id, p.name, si.quantity, si.unit_price, si.subtotal
                FROM sale_items si
                JOIN products p ON si.product_id = p.product_id
                WHERE si.sale_id = :sid
            """), {"sid": sale_id})
            rows = result.fetchall()
        
        items = [
            {
                "product_id": r[0],
                "product_name": r[1],
                "quantity": r[2],
                "unit_price": float(r[3]),
                "subtotal": float(r[4]) if r[4] else 0
            }
            for r in rows
        ]
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))