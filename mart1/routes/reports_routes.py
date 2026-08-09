"""
Report and analytics routes
"""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from db import engine

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/sales-by-date")
async def get_sales_by_date(days: int = 7):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT DATE(sale_time) as sale_date, COUNT(*) as count, SUM(total_amount) as total
                FROM sales
                WHERE sale_time >= CURRENT_DATE - CAST(:days || ' days' AS INTERVAL)
                GROUP BY DATE(sale_time)
                ORDER BY sale_date ASC
            """), {"days": days})
            rows = result.fetchall()

        data = [
            {"date": str(r[0]), "count": r[1], "total": float(r[2]) if r[2] else 0}
            for r in rows
        ]
        return {"sales_by_date": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_data(days: int = 7):
    try:
        with engine.connect() as conn:
            sales_by_date = conn.execute(text(f"""
                SELECT DATE(sale_time) as date, COUNT(*) as count, SUM(total_amount) as total
                FROM sales
                WHERE sale_time >= CURRENT_DATE - CAST('{days}' AS INTEGER || ' days')::INTERVAL
                GROUP BY DATE(sale_time)
                ORDER BY date ASC
            """))
            sales_data = [
                {"date": str(r[0]), "count": r[1], "total": float(r[2]) if r[2] else 0}
                for r in sales_by_date
            ]

            category_sales = conn.execute(text("""
                SELECT c.name, SUM(si.subtotal) as total_sales
                FROM categories c
                LEFT JOIN products p ON c.category_id = p.category_id
                LEFT JOIN sale_items si ON p.product_id = si.product_id
                GROUP BY c.category_id, c.name
                HAVING SUM(si.subtotal) > 0
                ORDER BY SUM(si.subtotal) DESC
            """))
            category_data = [
                {"category": r[0], "value": float(r[1]) if r[1] else 0}
                for r in category_sales
            ]

            top_products = conn.execute(text("""
                SELECT p.name, SUM(si.quantity) as total_quantity, SUM(si.subtotal) as total_revenue
                FROM products p
                JOIN sale_items si ON p.product_id = si.product_id
                GROUP BY p.product_id, p.name
                ORDER BY total_revenue DESC
                LIMIT 5
            """))
            products_data = [
                {
                    "product": r[0],
                    "quantity": r[1],
                    "revenue": float(r[2]) if r[2] else 0
                }
                for r in top_products
            ]

            return {
                "sales_by_date": sales_data,
                "category_sales": category_data,
                "top_products": products_data
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category-sales")
async def get_category_sales():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT c.name, SUM(si.subtotal) as total_sales
                FROM categories c
                LEFT JOIN products p ON c.category_id = p.category_id
                LEFT JOIN sale_items si ON p.product_id = si.product_id
                GROUP BY c.category_id, c.name
                HAVING SUM(si.subtotal) > 0
                ORDER BY SUM(si.subtotal) DESC
            """))
            rows = result.fetchall()

        data = [
            {"category": r[0], "value": float(r[1]) if r[1] else 0}
            for r in rows
        ]
        return {"category_sales": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-products")
async def get_top_products(limit: int = 5):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT p.name, SUM(si.quantity) as total_quantity, SUM(si.subtotal) as total_revenue
                FROM products p
                JOIN sale_items si ON p.product_id = si.product_id
                GROUP BY p.product_id, p.name
                ORDER BY total_revenue DESC
                LIMIT :limit
            """), {"limit": limit})
            rows = result.fetchall()

        data = [
            {
                "product": r[0],
                "quantity": r[1],
                "revenue": float(r[2]) if r[2] else 0
            }
            for r in rows
        ]
        return {"top_products": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-time-analysis")
async def get_all_time_analysis():
    try:
        with engine.connect() as conn:
            all_time_revenue = conn.execute(text("""
                SELECT COALESCE(SUM(total_amount), 0) as total_revenue
                FROM sales
            """)).scalar()

            all_time_transactions = conn.execute(text("""
                SELECT COUNT(*) as total_transactions
                FROM sales
            """)).scalar()

            avg_transaction_value = conn.execute(text("""
                SELECT COALESCE(AVG(total_amount), 0) as avg_value
                FROM sales
            """)).scalar()

            monthly_revenue_result = conn.execute(text("""
                SELECT TO_CHAR(sale_time, 'YYYY-MM') as month, COALESCE(SUM(total_amount), 0) as revenue
                FROM sales
                GROUP BY TO_CHAR(sale_time, 'YYYY-MM')
                ORDER BY month DESC
                LIMIT 12
            """))
            monthly_revenue = [
                {"month": r[0], "revenue": float(r[1]) if r[1] else 0}
                for r in monthly_revenue_result.fetchall()
            ]

        return {
            "all_time_revenue": float(all_time_revenue or 0),
            "all_time_transactions": all_time_transactions or 0,
            "avg_transaction_value": float(avg_transaction_value or 0),
            "monthly_revenue": monthly_revenue
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))