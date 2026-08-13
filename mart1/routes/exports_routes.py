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
    """
    Export sales line-items for analytics.
    Filters by date first, then joins — much faster on large tables.
    """
    try:
        limit = max(1, min(int(limit or 1000), 5000))
        params = {"limit": limit}

        # Filter sales first (uses sale_time index if present), then join details
        where_clause = ""
        if days is not None and int(days) > 0:
            where_clause = "WHERE s.sale_time >= CURRENT_DATE - CAST(:days AS INTEGER) * INTERVAL '1 day'"
            params["days"] = int(days)

        query = f"""
            SELECT
                CONCAT(s.sale_id, '-', si.sale_item_id) AS "Invoice ID",
                TO_CHAR(s.sale_time, 'YYYY-MM-DD') AS "Date",
                TO_CHAR(s.sale_time, 'HH24:MI') AS "Time",
                COALESCE(si.quantity * si.unit_price, 0) AS "Total",
                COALESCE(si.quantity, 0) AS "Quantity",
                COALESCE(si.unit_price, 0) AS "Unit price",
                COALESCE(cat.name, 'Uncategorized') AS "Product line",
                COALESCE(s.payment_method, 'Unknown') AS "Payment",
                CASE WHEN s.customer_id IS NOT NULL THEN 'Member' ELSE 'Normal' END AS "Customer type",
                COALESCE(p.name, 'Unknown') AS "Product name",
                COALESCE(cat.name, 'Uncategorized') AS "Category",
                COALESCE(cust.gender, 'Unknown') AS "Gender",
                COALESCE(s.discount_percentage, 0) AS "Discount (%)",
                s.customer_rating AS "Customer_Rating",
                s.feedback AS "Feedback",
                COALESCE(cust.churn, 0) AS "Churn"
            FROM (
                SELECT sale_id, sale_time, payment_method, customer_id,
                       discount_percentage, customer_rating, feedback
                FROM sales s
                {where_clause}
                ORDER BY s.sale_time DESC
                LIMIT :limit
            ) s
            INNER JOIN sale_items si ON si.sale_id = s.sale_id
            LEFT JOIN products p ON p.product_id = si.product_id
            LEFT JOIN categories cat ON cat.category_id = p.category_id
            LEFT JOIN customers cust ON cust.customer_id = s.customer_id
            ORDER BY s.sale_time DESC
            LIMIT :limit
        """

        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            rows = result.mappings().all()

        sales_data = []
        for r in rows:
            sales_data.append({
                "Invoice ID": r["Invoice ID"],
                "Date": r["Date"],
                "Time": r["Time"],
                "Total": float(r["Total"] or 0),
                "Quantity": int(r["Quantity"] or 0),
                "Unit price": float(r["Unit price"] or 0),
                "Product line": r["Product line"],
                "Payment": r["Payment"],
                "Customer type": r["Customer type"],
                "Product name": r["Product name"],
                "Category": r["Category"],
                "Gender": r["Gender"],
                "Discount (%)": float(r["Discount (%)"] or 0),
                "Customer_Rating": float(r["Customer_Rating"]) if r["Customer_Rating"] is not None else None,
                "Feedback": r["Feedback"],
                "Churn": int(r["Churn"] or 0),
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
