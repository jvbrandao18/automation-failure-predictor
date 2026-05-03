import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./automation_failures.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
pool_args = {"poolclass": StaticPool} if DATABASE_URL == "sqlite://" else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, **pool_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
