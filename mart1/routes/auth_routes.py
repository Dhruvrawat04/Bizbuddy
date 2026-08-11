"""
Authentication routes for login and token verification
"""
from fastapi import APIRouter, HTTPException, Header, Request
from sqlalchemy import text
from datetime import datetime as dt, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
import os

from db import engine
from models import LoginRequest, LoginResponse, TokenData
from routes.async_utils import async_route
from routes.audit_helper import write_audit

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-12345678")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

router = APIRouter(prefix="/api/auth", tags=["authentication"])


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = dt.utcnow() + expires_delta
    else:
        expire = dt.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.get("/health")
@async_route
def auth_health():
    """Check if auth routes are loaded"""
    return {"status": "ok", "message": "Auth routes loaded successfully"}


@router.post("/login", response_model=LoginResponse)
@async_route
def login(credentials: LoginRequest, request: Request):
    """
    Authenticate user with username and password.
    Returns JWT access token and user information.
    """
    try:
        print(f"Login attempt for username: {credentials.username}")
        with engine.connect() as conn:
            # First check if user exists
            res = conn.execute(text("""
                SELECT COUNT(*) FROM employees
            """))
            total = res.fetchone()[0]
            print(f"Total employees in database: {total}")
            
            # Try to find the user
            res = conn.execute(text("""
                SELECT employee_id, name, role, password
                FROM employees
                WHERE LOWER(username) = LOWER(:uname)
            """), {"uname": credentials.username})
            row = res.fetchone()
            
            if not row:
                write_audit(
                    action="LOGIN",
                    username=credentials.username,
                    status="FAILED",
                    error_message="Invalid username",
                    request=request,
                )
                print(f"Login attempt failed for username: {credentials.username}")
                res = conn.execute(text("""
                    SELECT username FROM employees
                """))
                existing = [r[0] for r in res]
                print(f"Existing usernames: {existing}")
                raise HTTPException(status_code=401, detail="Invalid username")
        
        emp_id, name, role, stored_password = row
        
        # Verify password using bcrypt
        try:
            if not bcrypt.checkpw(credentials.password.encode('utf-8'), stored_password.encode('utf-8')):
                write_audit(
                    action="LOGIN",
                    table_name="employees",
                    record_id=emp_id,
                    username=credentials.username,
                    role=role,
                    status="FAILED",
                    error_message="Invalid password",
                    actor={"user_id": emp_id, "username": credentials.username, "role": role},
                    request=request,
                )
                print(f"Password verification failed for {credentials.username}")
                raise HTTPException(status_code=401, detail="Invalid password")
        except Exception as e:
            # If bcrypt fails (e.g., plain text password in DB), try plain text comparison as fallback
            print(f"Bcrypt verification failed, trying plain text: {e}")
            if credentials.password != stored_password:
                write_audit(
                    action="LOGIN",
                    table_name="employees",
                    record_id=emp_id,
                    username=credentials.username,
                    role=role,
                    status="FAILED",
                    error_message="Invalid password",
                    actor={"user_id": emp_id, "username": credentials.username, "role": role},
                    request=request,
                )
                print(f"Plain text password verification also failed for {credentials.username}")
                raise HTTPException(status_code=401, detail="Invalid password")
        
        # Create JWT token
        access_token = create_access_token(
            data={"sub": str(emp_id), "role": role}
        )

        write_audit(
            action="LOGIN",
            table_name="employees",
            record_id=emp_id,
            status="SUCCESS",
            actor={"user_id": emp_id, "username": credentials.username, "role": role},
            request=request,
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            employee_id=emp_id,
            name=name,
            role=role,
            message=f"Welcome {name}!"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify")
@async_route
def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token and return current user data"""
    try:
        if authorization is None:
            raise HTTPException(status_code=401, detail="No token provided")
        
        # Extract token from "Bearer <token>"
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        employee_id: int = int(payload.get("sub")) if payload.get("sub") else None
        role: str = payload.get("role")
        
        if employee_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        with engine.connect() as conn:
            res = conn.execute(text("""
                SELECT employee_id, name, role
                FROM employees
                WHERE employee_id = :emp_id
            """), {"emp_id": employee_id})
            row = res.fetchone()
        
        if not row:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {
            "employee_id": row[0],
            "name": row[1],
            "role": row[2],
            "valid": True
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))