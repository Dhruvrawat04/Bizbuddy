"""
Employee management routes
"""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
import math
import bcrypt

from db import engine
from models import Employee

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.get("")
async def get_employees(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(50, ge=1, le=500, description="Number of items per page (max 500)")
):
    """Get all employees with pagination"""
    try:
        with engine.connect() as conn:
            # Get total count
            count_result = conn.execute(text("SELECT COUNT(*) FROM employees"))
            total_items = count_result.fetchone()[0]
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = math.ceil(total_items / page_size)
            
            result = conn.execute(text("""
                SELECT employee_id, name, role, username 
                FROM employees 
                ORDER BY name
                LIMIT :limit OFFSET :offset
            """), {"limit": page_size, "offset": offset})
            rows = result.fetchall()
        
        employees = [
            {"employee_id": r[0], "name": r[1], "role": r[2], "username": r[3]}
            for r in rows
        ]
        return {
            "employees": employees,
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
async def add_employee(employee: Employee):
    """Add a new employee"""
    try:
        hashed_password = bcrypt.hashpw(employee.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT INTO employees (name, role, username, password)
                VALUES (:name, :role, :username, :password)
                RETURNING employee_id
            """), {
                "name": employee.name,
                "role": employee.role,
                "username": employee.username,
                "password": hashed_password
            })
            employee_id = result.fetchone()[0]
            
        return {"message": "Employee added successfully", "employee_id": employee_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))