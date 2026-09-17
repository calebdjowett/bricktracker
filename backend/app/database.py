import sqlite3
from collections.abc import Generator
from pathlib import Path

DATABASE_PATH = Path(__file__).parents[2] / "data" / "bricktracker.sqlite3"


def initialize_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    schema_path = Path(__file__).parents[2] / "database" / "schema.sql"
    with sqlite3.connect(DATABASE_PATH) as database:
        database.executescript(schema_path.read_text())


def get_database() -> Generator[sqlite3.Connection, None, None]:
    database = sqlite3.connect(DATABASE_PATH)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys = ON")
    try:
        yield database
    finally:
        database.close()
