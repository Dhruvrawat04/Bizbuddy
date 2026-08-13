import os
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

load_dotenv()

DB_HOST = os.getenv(
    "PGHOST",
    "aws-1-ap-southeast-1.pooler.supabase.com"
)

DB_PORT = int(os.getenv("PGPORT", "5432"))
DB_NAME = os.getenv("PGDATABASE", "postgres")
DB_USER = os.getenv(
    "PGUSER",
    "postgres.maiayxnydpqptikawkhs"
)
DB_PASS = os.getenv("PGPASSWORD", "")


def get_connection():
    try:
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            sslmode="require"
        )
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def get_connection_string():
    return URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        query={"sslmode": "require"}
    )


def get_engine():
    try:
        print(
            f"DB connect → "
            f"host={DB_HOST} "
            f"port={DB_PORT} "
            f"db={DB_NAME} "
            f"user={DB_USER}"
        )

        if not DB_PASS:
            print("WARNING: PGPASSWORD is empty")

        return create_engine(
            get_connection_string(),
            echo=False,
            pool_size=5,
            max_overflow=5,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            echo_pool=False
        )

    except Exception as e:
        print(f"Error creating SQLAlchemy engine: {e}")
        return None


engine = get_engine()
