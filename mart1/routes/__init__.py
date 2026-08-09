"""
Routes package containing all API route definitions
"""
from .auth_routes import router as auth_router
from .products_routes import router as products_router
from .categories_routes import router as categories_router
from .suppliers_routes import router as suppliers_router
from .sales_routes import router as sales_router
from .customers_routes import router as customers_router
from .employees_routes import router as employees_router
from .purchase_orders_routes import router as purchase_orders_router
from .dashboard_routes import router as dashboard_router
from .notifications_routes import router as notifications_router
from .reports_routes import router as reports_router
from .exports_routes import router as exports_router
from .audit_logs_routes import router as audit_logs_router

__all__ = [
    "auth_router",
    "products_router",
    "categories_router",
    "suppliers_router",
    "sales_router",
    "customers_router",
    "employees_router",
    "purchase_orders_router",
    "dashboard_router",
    "notifications_router",
    "reports_router",
    "exports_router",
    "audit_logs_router",
]