from collections.abc import Generator
import os
from pathlib import Path

from psycopg import Connection, connect
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get("DATABASE_URL")


def connection() -> Connection:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL must be configured with the Supabase Postgres connection string.")
    return connect(DATABASE_URL, row_factory=dict_row)


def initialize_database() -> None:
    schema_path = Path(__file__).parents[2] / "database" / "schema.sql"
    with connection() as database:
        database.execute(schema_path.read_text())


def get_database() -> Generator[Connection, None, None]:
    database = connection()
    try:
        yield database
        database.commit()
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()
