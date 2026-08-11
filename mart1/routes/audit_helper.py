"""Shared helpers for writing audit log entries from API routes."""

from typing import Any, Optional

from fastapi import Request
from jose import JWTError, jwt
from sqlalchemy import text

from audit_system import log_activity
from db import engine

import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-12345678")
ALGORITHM = "HS256"


def _lookup_employee(employee_id: int) -> Optional[dict]:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT employee_id, username, role
                FROM employees
                WHERE employee_id = :employee_id
                """
            ),
            {"employee_id": employee_id},
        ).fetchone()

    if not row:
        return None

    return {
        "user_id": row[0],
        "username": row[1],
        "role": row[2],
    }


def resolve_actor(
    authorization: Optional[str] = None,
    employee_id: Optional[int] = None,
    username: Optional[str] = None,
    role: Optional[str] = None,
) -> dict:
    """Resolve the acting user from JWT token and/or explicit identifiers."""
    actor = {
        "user_id": employee_id,
        "username": username,
        "role": role,
    }

    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                actor["user_id"] = int(payload["sub"]) if payload.get("sub") else actor["user_id"]
                actor["role"] = payload.get("role") or actor["role"]
            except (JWTError, TypeError, ValueError):
                pass

    if actor["user_id"] and (not actor["username"] or not actor["role"]):
        employee = _lookup_employee(actor["user_id"])
        if employee:
            actor.update(employee)

    return actor


def write_audit(
    action: str,
    table_name: Optional[str] = None,
    record_id: Optional[int] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    status: str = "SUCCESS",
    error_message: Optional[str] = None,
    actor: Optional[dict] = None,
    request: Optional[Request] = None,
):
    """Write one audit log row. Failures are swallowed so core actions still succeed."""
    ip_address = None
    user_agent = None
    if request is not None:
        if request.client:
            ip_address = request.client.host
        user_agent = request.headers.get("user-agent")

    actor = actor or {}

    log_activity(
        user_id=actor.get("user_id"),
        username=actor.get("username"),
        role=actor.get("role"),
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        error_message=error_message,
    )


def model_to_dict(model: Any) -> dict:
    if hasattr(model, "model_dump"):
        data = model.model_dump()
    elif hasattr(model, "dict"):
        data = model.dict()
    else:
        data = dict(model)

    sanitized = {}
    for key, value in data.items():
        if key == "password":
            sanitized[key] = "***"
        else:
            sanitized[key] = value
    return sanitized
