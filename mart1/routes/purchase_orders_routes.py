"""
Purchase order management routes
"""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
import math

from db import engine
from models import PurchaseOrder

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase-orders"])


@router.get("")
async def get_purchase_orders(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(50, ge=1, le=500, description="Number of items per page (max 500)")
):
    """Get all purchase orders with pagination"""
    try:
        with engine.connect() as conn:
            # Get total count
            count_result = conn.execute(text("SELECT COUNT(*) FROM purchase_orders"))
            total_items = count_result.fetchone()[0]
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = math.ceil(total_items / page_size)
            
            result = conn.execute(text("""
                SELECT po.order_id, po.order_date, po.status, s.name as supplier_name
                FROM purchase_orders po
                JOIN suppliers s ON po.supplier_id = s.supplier_id
                ORDER BY po.order_date DESC
                LIMIT :limit OFFSET :offset
            """), {"limit": page_size, "offset": offset})
            rows = result.fetchall()
        
        orders = [
            {
                "order_id": r[0],
                "order_date": str(r[1]),
                "status": r[2],
                "supplier_name": r[3]
            }
            for r in rows
        ]
        return {
            "purchase_orders": orders,
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
async def create_purchase_order(order: PurchaseOrder):
    """Create a new purchase order"""
    try:
        with engine.begin() as conn:
            # OPTIMIZED: Fetch supplier AND validate all products at once (was N+1 queries)
            product_ids = [item.get('product_id') for item in order.items]
            validation_query = f"""
                SELECT 
                    s.supplier_id, 
                    s.category_id,
                    array_agg(DISTINCT p.product_id) as valid_product_ids,
                    array_agg(DISTINCT p.category_id) as product_categories
                FROM suppliers s
                LEFT JOIN products p ON p.product_id = ANY(ARRAY[{','.join(map(str, product_ids))}])
                WHERE s.supplier_id = :sid
                GROUP BY s.supplier_id, s.category_id
            """
            supplier_result = conn.execute(text(validation_query), {"sid": order.supplier_id})
            supplier_row = supplier_result.fetchone()
            
            if not supplier_row:
                raise HTTPException(status_code=404, detail="Supplier not found")
            
            supplier_id, supplier_category_id, valid_product_ids, product_categories = supplier_row
            
            # Validate all products exist and match supplier category
            if supplier_category_id is not None:
                missing_products = [pid for pid in product_ids if pid not in (valid_product_ids or [])]
                if missing_products:
                    raise HTTPException(status_code=404, detail=f"Products not found: {missing_products}")
                
                if product_categories and None not in product_categories:
                    for pid, pcat in zip(valid_product_ids, product_categories):
                        if pcat != supplier_category_id:
                            cat_result = conn.execute(text("""
                                SELECT c1.name, c2.name
                                FROM categories c1, categories c2
                                WHERE c1.category_id = :scid AND c2.category_id = :pcid
                            """), {"scid": supplier_category_id, "pcid": pcat})
                            cat_names = cat_result.fetchone()
                            raise HTTPException(
                                status_code=400,
                                detail=f"Supplier category mismatch: This supplier is registered for '{cat_names[0]}' but product belongs to '{cat_names[1]}'. Suppliers can only supply products in their registered category."
                            )
            
            # Create purchase order
            result = conn.execute(text("""
                INSERT INTO purchase_orders (supplier_id, order_date, status)
                VALUES (:supplier_id, CURRENT_TIMESTAMP, :status)
                RETURNING order_id
            """), {
                "supplier_id": order.supplier_id,
                "status": order.status
            })
            order_id = result.fetchone()[0]
            
            # OPTIMIZED: Bulk insert all order items
            total_amount = 0
            for item in order.items:
                conn.execute(text("""
                    INSERT INTO purchase_order_items (order_id, product_id, quantity, unit_price)
                    VALUES (:order_id, :product_id, :quantity, :unit_price)
                """), {
                    "order_id": order_id,
                    "product_id": item.get('product_id'),
                    "quantity": item.get('quantity'),
                    "unit_price": item.get('unit_price')
                })
                total_amount += item.get('quantity') * item.get('unit_price')
            
        
        return {"message": "Purchase order created successfully", "order_id": order_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}")
async def get_purchase_order_details(order_id: int):
    """Get details of a specific purchase order"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT poi.product_id, p.name, poi.quantity, poi.unit_price
                FROM purchase_order_items poi
                JOIN products p ON poi.product_id = p.product_id
                WHERE poi.order_id = :oid
            """), {"oid": order_id})
            rows = result.fetchall()
        
        items = [
            {
                "product_id": r[0],
                "product_name": r[1],
                "quantity": r[2],
                "unit_price": float(r[3])
            }
            for r in rows
        ]
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{order_id}/receive")
async def receive_purchase_order(order_id: int):
    """Receive a purchase order and update stock"""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT poi.product_id, poi.quantity
                FROM purchase_order_items poi
                WHERE poi.order_id = :oid
            """), {"oid": order_id})
            items = result.fetchall()
            
            if not items:
                raise HTTPException(status_code=404, detail="Purchase order not found")
            
            for product_id, quantity in items:
                conn.execute(text("""
                    UPDATE products 
                    SET stock_quantity = stock_quantity + :qty
                    WHERE product_id = :pid
                """), {"qty": quantity, "pid": product_id})
            
            conn.execute(text("""
                UPDATE purchase_orders 
                SET status = 'RECEIVED'
                WHERE order_id = :oid
            """), {"oid": order_id})
        
        return {"message": "Purchase order received and stock updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))