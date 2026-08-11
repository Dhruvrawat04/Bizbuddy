"""
Notification routes
"""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
import math

from db import engine
from models import NotificationUpdate
from routes.async_utils import async_route

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
@async_route
def get_notifications(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(50, ge=1, le=500, description="Number of items per page (max 500)")
):
    try:
        with engine.connect() as conn:
            count_result = conn.execute(text("SELECT COUNT(*) FROM notifications"))
            total_items = count_result.fetchone()[0]

            offset = (page - 1) * page_size
            total_pages = math.ceil(total_items / page_size)

            result = conn.execute(text("""
                SELECT n.notification_id, n.message, n.status, n.notification_type,
                       n.created_at, p.name as product_name
                FROM notifications n
                LEFT JOIN products p ON n.product_id = p.product_id
                ORDER BY n.created_at DESC
                LIMIT :limit OFFSET :offset
            """), {"limit": page_size, "offset": offset})
            rows = result.fetchall()

        notifications = [
            {
                "notification_id": r[0],
                "message": r[1],
                "status": r[2],
                "type": r[3],
                "created_at": str(r[4]),
                "product_name": r[5]
            }
            for r in rows
        ]
        return {
            "notifications": notifications,
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


@router.put("/{notification_id}")
@async_route
def update_notification(notification_id: int, notification: NotificationUpdate):
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                UPDATE notifications
                SET status = :status, read_at = CASE WHEN :status = 'read' THEN NOW() ELSE read_at END
                WHERE notification_id = :nid
                RETURNING notification_id
            """), {"status": notification.status, "nid": notification_id})
            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Notification not found")
        return {"message": "Notification updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))