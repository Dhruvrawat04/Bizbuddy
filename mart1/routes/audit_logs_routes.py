"""
Audit log routes
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from audit_system import get_recent_logs, get_user_activity, get_suspicious_activities, generate_audit_report

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])


def _check_role(user_role: Optional[str]):
    if user_role not in ["ADMIN", "MANAGER"]:
        raise HTTPException(status_code=403, detail="Access denied. Admin or Manager role required.")


@router.get("")
async def get_audit_logs(limit: int = 50, user_role: str = None):
    _check_role(user_role)
    try:
        logs = get_recent_logs(limit)
        return {"data": logs, "count": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
async def get_user_audit_logs(user_id: int, days: int = 7, user_role: str = None):
    _check_role(user_role)
    try:
        activity = get_user_activity(user_id, days)
        return {"data": [dict(row._mapping) for row in activity]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suspicious")
async def get_suspicious_activities_route(user_role: str = None):
    _check_role(user_role)
    try:
        alerts = get_suspicious_activities()
        return {
            "failed_logins": [dict(row._mapping) for row in alerts["failed_logins"]],
            "after_hours_activity": [dict(row._mapping) for row in alerts["after_hours_activity"]],
            "bulk_deletions": [dict(row._mapping) for row in alerts["bulk_deletions"]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def get_audit_report(start_date: Optional[str] = None, end_date: Optional[str] = None, user_role: str = None):
    _check_role(user_role)
    try:
        report = generate_audit_report(start_date, end_date)
        return {
            "statistics": [dict(row._mapping) for row in report["statistics"]],
            "top_users": [dict(row._mapping) for row in report["top_users"]],
            "table_activity": [dict(row._mapping) for row in report["table_activity"]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))