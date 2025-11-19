import os
from sqlalchemy import create_engine
import urllib.parse

# Supabase PostgreSQL Configuration
DB_HOST = os.getenv("PGHOST", "aws-1-ap-southeast-2.pooler.supabase.com")
DB_NAME = os.getenv("PGDATABASE", "postgres")
DB_USER = os.getenv("PGUSER", "postgres.xfdnitgnewcjicojwpdp")
DB_PASS = os.getenv("PGPASSWORD", "ZXCV@123")
DB_PORT = os.getenv("PGPORT", "5432")

# URL encode special characters in password for SQLAlchemy
encoded_pass = urllib.parse.quote_plus(DB_PASS)
CONNECTION_STRING = f"postgresql+psycopg2://{DB_USER}:{encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_connection_string():
    """Returns the PostgreSQL connection string for SQLAlchemy"""
    return CONNECTION_STRING


def get_engine():
    """Creates and returns a SQLAlchemy engine instance"""
    try:
        engine = create_engine(get_connection_string(), echo=False, pool_pre_ping=True)
        return engine
    except Exception as e:
        print(f"Error creating SQLAlchemy engine: {e}")
        return None
