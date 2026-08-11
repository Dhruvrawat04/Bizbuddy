from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
import os

import psycopg2
from dotenv import load_dotenv


load_dotenv()


def connect():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        parsed = urlparse(database_url)
        connect_kwargs = {
            "dbname": parsed.path.lstrip("/"),
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
        }
        query_params = {
            key: values[-1]
            for key, values in parse_qs(parsed.query).items()
            if values
        }
        connect_kwargs.update(query_params)
        if parsed.hostname and parsed.hostname not in {"localhost", "127.0.0.1"}:
            connect_kwargs.setdefault("sslmode", "require")

        return psycopg2.connect(**connect_kwargs)

    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        database=os.getenv("PGDATABASE", "mart_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", ""),
        port=os.getenv("PGPORT", "5432"),
    )


def main():
    schema_path = Path(__file__).with_name("schema[1].sql")
    schema_sql = schema_path.read_text(encoding="utf-8")

    conn = connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.employees');")
            if cursor.fetchone()[0]:
                print("Database schema already exists; skipping initialization.")
                return

            cursor.execute(schema_sql)
            conn.commit()
            print("Database schema initialized successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()