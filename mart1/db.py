import os
import urllib.parse
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv(Path(__file__).resolve().parent / ".env")

# Supabase pooler defaults for this project
DEFAULT_HOST = "aws-1-ap-southeast-1.pooler.supabase.com"
DEFAULT_USER = "postgres.maiayxnydpqptikawkhs"
DEFAULT_PORT = "6543"

DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST = os.getenv("PGHOST", DEFAULT_HOST)
DB_NAME = os.getenv("PGDATABASE", "postgres")
DB_USER = os.getenv("PGUSER", DEFAULT_USER)
DB_PASS = os.getenv("PGPASSWORD", "")
DB_PORT = os.getenv("PGPORT", DEFAULT_PORT)

# Pooler requires user = postgres.<project-ref>, not plain "postgres"
if DB_USER == "postgres":
    DB_USER = DEFAULT_USER
    print(f"PGUSER was 'postgres'; using pooler user '{DB_USER}' instead")


def _build_url_from_pg_vars():
    encoded_pass = urllib.parse.quote_plus(DB_PASS)
    return (
        f"postgresql+psycopg2://{DB_USER}:{encoded_pass}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
    )


def _normalize_database_url(url: str) -> str:
    """Ensure SQLAlchemy driver prefix and sslmode."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


# Prefer explicit PG* vars when password is set (avoids stale DATABASE_URL user=postgres)
if DB_PASS:
    CONNECTION_STRING = _build_url_from_pg_vars()
elif DATABASE_URL:
    CONNECTION_STRING = _normalize_database_url(DATABASE_URL)
else:
    CONNECTION_STRING = _build_url_from_pg_vars()


def get_connection():
    """Raw psycopg2 connection for direct SQL."""
    try:
        return psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=int(DB_PORT),
            sslmode="require",
        )
    except Exception as e:
        print(f"Error connecting with psycopg2: {e}")
        return None


def get_connection_string():
    return CONNECTION_STRING


def get_engine():
    try:
        print(
            f"DB connect → host={DB_HOST} port={DB_PORT} "
            f"db={DB_NAME} user={DB_USER}"
        )
        if not DB_PASS and not DATABASE_URL:
            print("WARNING: No PGPASSWORD or DATABASE_URL set")
        return create_engine(
            get_connection_string(),
            echo=False,
            pool_size=5,
            max_overflow=5,
            pool_timeout=10,
            pool_recycle=300,
            pool_pre_ping=True,
            echo_pool=False,
        )
    except Exception as e:
        print(f"Error creating SQLAlchemy engine: {e}")
        return None


engine = get_engine()
