"""
Dashboard and analytics routes
"""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from db import engine
from cache_layer import get_cached_or_fetch, CACHE_KEYS

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _fetch_dashboard_stats(conn, days: int) -> dict:
    if days == 0:
        result = conn.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM products) as total_products,
                (SELECT COUNT(*) FROM sales) as total_sales,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales) as total_revenue,
                (SELECT COUNT(*) FROM products WHERE stock_quantity <= low_stock_threshold) as low_stock_count,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE DATE(sale_time) = CURRENT_DATE) as today_sales
        """)).fetchone()
    else:
        result = conn.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM products) as total_products,
                (SELECT COUNT(*) FROM sales WHERE sale_time >= CURRENT_DATE - INTERVAL '1 day' * :days) as total_sales,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE sale_time >= CURRENT_DATE - INTERVAL '1 day' * :days) as total_revenue,
                (SELECT COUNT(*) FROM products WHERE stock_quantity <= low_stock_threshold) as low_stock_count,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE DATE(sale_time) = CURRENT_DATE) as today_sales
        """), {"days": days}).fetchone()

    return {
        "total_products": result[0],
        "total_sales": result[1],
        "total_revenue": float(result[2]),
        "low_stock_count": result[3],
        "today_sales": float(result[4]),
    }


def _fetch_sales_by_day(conn, days: int) -> list:
    if days == 0:
        q = text("""
            SELECT DATE(sale_time) as day, COALESCE(SUM(total_amount), 0) as total
            FROM sales
            GROUP BY DATE(sale_time)
            ORDER BY day
        """)
        rows = conn.execute(q).fetchall()
    else:
        q = text("""
            SELECT DATE(sale_time) as day, COALESCE(SUM(total_amount), 0) as total
            FROM sales
            WHERE sale_time >= CURRENT_DATE - INTERVAL '1 day' * :days
            GROUP BY DATE(sale_time)
            ORDER BY day
        """)
        rows = conn.execute(q, {"days": days}).fetchall()

    return [{"day": str(r[0]), "total": float(r[1])} for r in rows]


def _fetch_top_products(conn, days: int, limit: int = 5) -> list:
    if days == 0:
        q = text("""
            SELECT p.product_id, p.name, COALESCE(SUM(si.quantity * si.unit_price), 0) as revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            JOIN sales s ON si.sale_id = s.sale_id
            GROUP BY p.product_id, p.name
            ORDER BY revenue DESC
            LIMIT :limit
        """)
        rows = conn.execute(q, {"limit": limit}).fetchall()
    else:
        q = text("""
            SELECT p.product_id, p.name, COALESCE(SUM(si.quantity * si.unit_price), 0) as revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            JOIN sales s ON si.sale_id = s.sale_id
            WHERE s.sale_time >= CURRENT_DATE - INTERVAL '1 day' * :days
            GROUP BY p.product_id, p.name
            ORDER BY revenue DESC
            LIMIT :limit
        """)
        rows = conn.execute(q, {"limit": limit, "days": days}).fetchall()

    return [{"product_id": r[0], "name": r[1], "revenue": float(r[2])} for r in rows]


@router.get("/overview")
async def get_dashboard_overview(
    days: int = Query(0, ge=0, le=365, description="Number of days to look back (0 for all time)"),
    limit: int = Query(5, ge=1, le=50, description="Number of top products to return"),
):
    """Return stats, sales-by-day, and top products in a single request."""
    try:
        def fetch_overview():
            with engine.connect() as conn:
                return {
                    "stats": _fetch_dashboard_stats(conn, days),
                    "sales_by_day": _fetch_sales_by_day(conn, days),
                    "top_products": _fetch_top_products(conn, days, limit),
                }

        cache_key = f"dashboard:overview:{days}:{limit}"
        # Shorter cache for recent windows where users expect fresher numbers.
        ttl_seconds = 30 if days in (7, 14) else 60
        return get_cached_or_fetch(cache_key, fetch_overview, ttl_seconds=ttl_seconds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_dashboard_stats(days: int = Query(7, ge=0, le=365, description="Number of days to look back (0 for all time)")):
    """Get dashboard statistics"""
    try:
        def fetch_stats():
            with engine.connect() as conn:
                return _fetch_dashboard_stats(conn, days)
        
        # Cache key with days parameter to avoid cache conflicts
        cache_key = f"{CACHE_KEYS['DASHBOARD_STATS']}:{days}"
        ttl_seconds = 30 if days in (7, 14) else 60
        stats = get_cached_or_fetch(cache_key, fetch_stats, ttl_seconds=ttl_seconds)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales_by_day")
async def get_sales_by_day(days: int = Query(7, ge=0, le=365, description="Number of days to look back (0 for all time)")):
    """Return sales totals grouped by date for the given range"""
    try:
        def fetch_sales():
            with engine.connect() as conn:
                return _fetch_sales_by_day(conn, days)

        cache_key = CACHE_KEYS['SALES_BY_DATE'].format(days)
        ttl_seconds = 30 if days in (7, 14) else 60
        data = get_cached_or_fetch(cache_key, fetch_sales, ttl_seconds=ttl_seconds)
        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top_products")
async def get_top_products(
    limit: int = Query(5, ge=1, le=50, description="Number of top products to return"),
    days: int = Query(7, ge=0, le=365, description="Number of days to look back (0 for all time)")
):
    """Return top selling products by revenue, optionally filtered by recent days"""
    try:
        def fetch_top():
            with engine.connect() as conn:
                return _fetch_top_products(conn, days, limit)

        cache_key = CACHE_KEYS['TOP_PRODUCTS'].format(limit, days)
        ttl_seconds = 30 if days in (7, 14) else 60
        data = get_cached_or_fetch(cache_key, fetch_top, ttl_seconds=ttl_seconds)
        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))