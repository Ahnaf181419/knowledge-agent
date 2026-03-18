"""
Database session management.
"""

from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

DB_PATH = Path(__file__).parent.parent.parent / "knowledge_agent.db"

_engine = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False}
        )
    return _engine


def init_db() -> None:
    """Initialize database tables."""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    """Get a database session. Use as dependency."""
    engine = get_engine()
    with Session(engine) as session:
        yield session


def get_session_context() -> Session:
    """Get a session for use outside of dependency injection."""
    engine = get_engine()
    return Session(engine)
