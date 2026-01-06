"""
Database Activity Monitoring System
Tracks all database operations for security and compliance
"""
from sqlalchemy import text
from db import get_engine
from datetime import datetime
import json

def create_audit_table():
    """Creates the audit_logs table if it doesn't exist"""
    engine = get_engine()
    
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id SERIAL PRIMARY KEY,
                user_id INTEGER,
                username VARCHAR(50),
                role VARCHAR(20),
                action VARCHAR(10),
                table_name VARCHAR(50),
                record_id INTEGER,
                old_values JSONB,
                new_values JSONB,
                ip_address VARCHAR(45),
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'SUCCESS',
                error_message TEXT
            )
        """))
        
        # Create index for faster queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_logs(table_name);
            CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
        """))
    
    print("✅ Audit logs table created successfully")

def log_activity(
    user_id: int = None,
    username: str = None,
    role: str = None,
    action: str = None,
    table_name: str = None,
    record_id: int = None,
    old_values: dict = None,
    new_values: dict = None,
    ip_address: str = None,
    user_agent: str = None,
    status: str = "SUCCESS",
    error_message: str = None
):
    """
    Logs a database activity to the audit trail
    
    Args:
        user_id: ID of the user performing the action
        username: Username of the user
        role: Role of the user (ADMIN, MANAGER, CASHIER)
        action: Type of action (INSERT, UPDATE, DELETE, SELECT)
        table_name: Name of the table affected
        record_id: ID of the specific record affected
        old_values: Dictionary of values before change
        new_values: Dictionary of values after change
        ip_address: IP address of the user
        user_agent: Browser/client information
        status: SUCCESS or FAILED
        error_message: Error details if action failed
    """
    engine = get_engine()
    
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO audit_logs (
                    user_id, username, role, action, table_name, 
                    record_id, old_values, new_values, ip_address, 
                    user_agent, status, error_message
                )
                VALUES (
                    :user_id, :username, :role, :action, :table_name,
                    :record_id, :old_values, :new_values, :ip_address,
                    :user_agent, :status, :error_message
                )
            """), {
                "user_id": user_id,
                "username": username,
                "role": role,
                "action": action,
                "table_name": table_name,
                "record_id": record_id,
                "old_values": json.dumps(old_values) if old_values else None,
                "new_values": json.dumps(new_values) if new_values else None,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "status": status,
                "error_message": error_message
            })
    except Exception as e:
        print(f"⚠️ Failed to log activity: {e}")

def get_recent_logs(limit: int = 50):
    """Get recent audit logs"""
    engine = get_engine()
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                log_id, user_id, username, role, action, 
                table_name, record_id, old_values, new_values,
                timestamp, status
            FROM audit_logs
            ORDER BY timestamp DESC
            LIMIT :limit
        """), {"limit": limit})
        
        logs = []
        for row in result:
            # PostgreSQL JSONB columns return dict directly, no need for json.loads()
            old_vals = row[7] if row[7] else None
            new_vals = row[8] if row[8] else None
            
            logs.append({
                "log_id": row[0],
                "user_id": row[1],
                "username": row[2],
                "role": row[3],
                "action": row[4],
                "table_name": row[5],
                "record_id": row[6],
                "old_values": old_vals,
                "new_values": new_vals,
                "timestamp": str(row[9]),
                "status": row[10]
            })
        
        return logs

def get_user_activity(user_id: int, days: int = 7):
    """Get all activity for a specific user"""
    engine = get_engine()
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                action, table_name, timestamp, status, COUNT(*) as count
            FROM audit_logs
            WHERE user_id = :uid
            AND timestamp >= NOW() - INTERVAL ':days days'
            GROUP BY action, table_name, timestamp, status
            ORDER BY timestamp DESC
        """), {"uid": user_id, "days": days})
        
        return result.fetchall()

def get_suspicious_activities():
    """Detect suspicious patterns in audit logs"""
    engine = get_engine()
    
    with engine.connect() as conn:
        # Multiple failed login attempts
        result = conn.execute(text("""
            SELECT username, COUNT(*) as attempts, MAX(timestamp) as last_attempt
            FROM audit_logs
            WHERE action = 'LOGIN'
            AND status = 'FAILED'
            AND timestamp >= NOW() - INTERVAL '1 hour'
            GROUP BY username
            HAVING COUNT(*) >= 3
            ORDER BY attempts DESC
        """))
        
        failed_logins = result.fetchall()
        
        # After-hours activity
        result = conn.execute(text("""
            SELECT username, action, table_name, timestamp
            FROM audit_logs
            WHERE EXTRACT(HOUR FROM timestamp) NOT BETWEEN 6 AND 22
            AND action IN ('DELETE', 'UPDATE')
            AND timestamp >= NOW() - INTERVAL '7 days'
            ORDER BY timestamp DESC
        """))
        
        after_hours = result.fetchall()
        
        # Bulk deletions
        result = conn.execute(text("""
            SELECT username, table_name, COUNT(*) as delete_count, DATE(timestamp) as date
            FROM audit_logs
            WHERE action = 'DELETE'
            AND timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY username, table_name, DATE(timestamp)
            HAVING COUNT(*) >= 10
            ORDER BY delete_count DESC
        """))
        
        bulk_deletes = result.fetchall()
        
        return {
            "failed_logins": failed_logins,
            "after_hours_activity": after_hours,
            "bulk_deletions": bulk_deletes
        }

def generate_audit_report(start_date: str = None, end_date: str = None):
    """Generate comprehensive audit report"""
    engine = get_engine()
    
    with engine.connect() as conn:
        # Overall statistics
        stats = conn.execute(text("""
            SELECT 
                action,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed
            FROM audit_logs
            WHERE timestamp >= :start_date
            AND timestamp <= :end_date
            GROUP BY action
        """), {
            "start_date": start_date or '2000-01-01',
            "end_date": end_date or '2099-12-31'
        })
        
        # Most active users
        users = conn.execute(text("""
            SELECT 
                username, role,
                COUNT(*) as activities,
                MAX(timestamp) as last_activity
            FROM audit_logs
            WHERE timestamp >= :start_date
            AND timestamp <= :end_date
            GROUP BY username, role
            ORDER BY activities DESC
            LIMIT 10
        """), {
            "start_date": start_date or '2000-01-01',
            "end_date": end_date or '2099-12-31'
        })
        
        # Most modified tables
        tables = conn.execute(text("""
            SELECT 
                table_name,
                action,
                COUNT(*) as modifications
            FROM audit_logs
            WHERE action IN ('INSERT', 'UPDATE', 'DELETE')
            AND timestamp >= :start_date
            AND timestamp <= :end_date
            GROUP BY table_name, action
            ORDER BY modifications DESC
        """), {
            "start_date": start_date or '2000-01-01',
            "end_date": end_date or '2099-12-31'
        })
        
        return {
            "statistics": stats.fetchall(),
            "top_users": users.fetchall(),
            "table_activity": tables.fetchall()
        }

if __name__ == "__main__":
    print("🔧 Setting up Database Activity Monitoring...")
    create_audit_table()
    print("✅ Setup complete!")
