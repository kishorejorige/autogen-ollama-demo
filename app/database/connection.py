import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/autogen_demo.db")


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./data/autogen_demo.db")


def ensure_db_dir(url: str) -> None:
    if url.startswith("sqlite:///"):
        db_path_str = url.replace("sqlite:///", "")
        if db_path_str and db_path_str != ":memory:":
            db_path = Path(db_path_str)
            db_path.parent.mkdir(parents=True, exist_ok=True)


def create_db_engine(url: str | None = None) -> Engine:
    target_url = url or get_db_url()
    ensure_db_dir(target_url)

    connect_args = {}
    if target_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(target_url, connect_args=connect_args)

    if target_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


import logging

logger = logging.getLogger(__name__)


def init_db(target_engine: Engine | None = None) -> None:
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)

    with eng.connect() as conn:
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(conn)
            if "workflows" in inspector.get_table_names():
                columns = [c["name"] for c in inspector.get_columns("workflows")]
                if "favorite" not in columns:
                    conn.execute(text("ALTER TABLE workflows ADD COLUMN favorite BOOLEAN DEFAULT 0"))
                    conn.commit()
        except Exception as e:  # noqa: BLE001
            logger.debug("Migration notice: %s", e)


# Automatically create tables for the default engine
init_db(engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
