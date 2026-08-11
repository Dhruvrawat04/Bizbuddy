"""
Data export routes
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from typing import Optional

from db import engine
from routes.async_utils import async_route

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/sales")
@async_route
def export_sales_data(limit: int = 1000, days: Optional[int] = None):
    try:
        with engine.connect() as conn:
            query = """
                SELECT 
                    CONCAT(s.sale_id, '-', si.sale_item_id) as "Invoice ID",
                    s.sale_time::date as "Date",
                    s.sale_time::time as "Time",
                    (si.quantity * si.unit_price) as "Total",
                    si.quantity as "Quantity",
                    si.unit_price as "Unit price",
                    cat.name as "Product line",
                    s.payment_method as "Payment",
                    CASE WHEN cust.customer_id IS NOT NULL THEN 'Member' ELSE 'Normal' END as "Customer type",
                    p.name as "Product name",
                    cat.name as "Category",
                    COALESCE(cust.gender, 'Unknown') as "Gender",
                    COALESCE(s.discount_percentage, 0) as "Discount (%)",
                    s.customer_rating as "Customer_Rating",
                    s.feedback as "Feedback",
                    COALESCE(cust.churn, 0) as "Churn"
                FROM sales s
                LEFT JOIN sale_items si ON s.sale_id = si.sale_id
                LEFT JOIN products p ON si.product_id = p.product_id
                LEFT JOIN categories cat ON p.category_id = cat.category_id
                LEFT JOIN customers cust ON s.customer_id = cust.customer_id
            """

            if days:
                query += f" WHERE s.sale_time >= CURRENT_DATE - INTERVAL '{days} days'"

            query += f" ORDER BY s.sale_time DESC LIMIT {limit}"

            result = conn.execute(text(query))
            rows = result.fetchall()

        sales_data = []
        for r in rows:
            sales_data.append({
                "Invoice ID": r[0],
                "Date": str(r[1]),
                "Time": str(r[2]),
                "Total": float(r[3]) if r[3] else 0,
                "Quantity": r[4],
                "Unit price": float(r[5]) if r[5] else 0,
                "Product line": r[6],
                "Payment": r[7],
                "Customer type": r[8],
                "Product name": r[9],
                "Category": r[10],
                "Gender": r[11],
                "Discount (%)": float(r[12]) if r[12] else 0.0,
                "Customer_Rating": float(r[13]) if r[13] else None,
                "Feedback": r[14],
                "Churn": int(r[15]) if r[15] is not None else 0
            })

        return {"data": sales_data, "count": len(sales_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products")
@async_route
def export_products_data():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    p.product_id,
                    p.name,
                    p.price,
                    p.stock_quantity,
                    p.low_stock_threshold,
                    c.name as category,
                    s.name as supplier,
                    p.barcode
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.category_id
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
                ORDER BY p.product_id
            """))
            rows = result.fetchall()

        products = [
            {
                "product_id": r[0],
                "name": r[1],
                "price": float(r[2]) if r[2] else 0,
                "stock_quantity": r[3],
                "low_stock_threshold": r[4],
                "category": r[5],
                "supplier": r[6],
                "barcode": r[7]
            }
            for r in rows
        ]
        return {"data": products, "count": len(products)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories-performance")
@async_route
def export_category_performance(days: int = 30):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    c.name as category,
                    COUNT(DISTINCT s.sale_id) as transaction_count,
                    SUM(si.quantity) as total_quantity,
                    SUM(si.subtotal) as total_revenue,
                    AVG(si.subtotal) as avg_transaction_value
                FROM categories c
                LEFT JOIN products p ON c.category_id = p.category_id
                LEFT JOIN sale_items si ON p.product_id = si.product_id
                LEFT JOIN sales s ON si.sale_id = s.sale_id
                WHERE s.sale_time >= CURRENT_DATE - CAST(:days || ' days' AS INTERVAL)
                GROUP BY c.category_id, c.name
                HAVING SUM(si.subtotal) > 0
                ORDER BY total_revenue DESC
            """), {"days": days})
            rows = result.fetchall()

        categories = [
            {
                "category": r[0],
                "transaction_count": r[1],
                "total_quantity": r[2],
                "total_revenue": float(r[3]) if r[3] else 0,
                "avg_transaction_value": float(r[4]) if r[4] else 0
            }
            for r in rows
        ]
        return {"data": categories, "count": len(categories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory-status")
@async_route
def export_inventory_status():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    p.product_id,
                    p.name,
                    p.stock_quantity,
                    p.low_stock_threshold,
                    CASE 
                        WHEN p.stock_quantity <= p.low_stock_threshold THEN 'Low Stock'
                        WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                        ELSE 'Normal'
                    END as status,
                    c.name as category,
                    s.name as supplier
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.category_id
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
                ORDER BY p.stock_quantity ASC
            """))
            rows = result.fetchall()

        inventory = [
            {
                "product_id": r[0],
                "name": r[1],
                "stock_quantity": r[2],
                "low_stock_threshold": r[3],
                "status": r[4],
                "category": r[5],
                "supplier": r[6]
            }
            for r in rows
        ]
        return {"data": inventory, "count": len(inventory)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))