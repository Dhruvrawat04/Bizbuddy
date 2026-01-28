import os
from sqlalchemy import create_engine
import psycopg2
import urllib.parse

# Supabase PostgreSQL Configuration
# Database credentials from environment variables
DB_HOST = os.getenv("PGHOST", "db.maiayxnydpqptikawkhs.supabase.co")
DB_NAME = os.getenv("PGDATABASE", "postgres")
DB_USER = os.getenv("PGUSER", "postgres")
DB_PASS = os.getenv("PGPASSWORD", "Qwer@#_123456789012")
DB_PORT = os.getenv("PGPORT", "5432")

# URL encode special characters in password for SQLAlchemy
encoded_pass = urllib.parse.quote_plus(DB_PASS)
CONNECTION_STRING = f"postgresql+psycopg2://{DB_USER}:{encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_connection():
    """
    Establishes a raw psycopg2 connection (for direct SQL execution).
    Use only if you need low-level cursor operations.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Error connecting with psycopg2: {e}")
        return None


def get_connection_string():
    """
    Returns a SQLAlchemy-compatible connection string.
    Example format:
    postgresql+psycopg2://user:password@host:port/database
    """
    return CONNECTION_STRING


def get_engine():
    """
    Creates and returns a SQLAlchemy engine instance with optimized connection pooling.
    
    Pool Configuration:
    - pool_size: 50 - Number of persistent connections to keep open (increased for production)
    - max_overflow: 20 - Additional connections that can be created beyond pool_size
    - pool_timeout: 5 - Seconds to wait before giving up on getting a connection (reduced for faster failure)
    - pool_recycle: 3600 - Recycle connections after 1 hour to prevent stale connections
    - pool_pre_ping: True - Test connections before using them
    - echo_pool: False - Disable connection pool logging for performance
    """
    try:
        engine = create_engine(
            get_connection_string(),
            echo=False,
            pool_size=50,              # Maintain 50 persistent connections (optimized for production)
            max_overflow=20,           # Allow 20 additional connections under load (total: 70)
            pool_timeout=5,            # Wait up to 5 seconds for an available connection (fail fast)
            pool_recycle=3600,         # Recycle connections every hour
            pool_pre_ping=True,        # Verify connection health before use
            echo_pool=False            # Disable pool logging for performance
        )
        return engine
    except Exception as e:
        print(f"Error creating SQLAlchemy engine: {e}")
        return None


# Singleton engine instance - shared across all modules to prevent duplicate connection pools
engine = get_engine()