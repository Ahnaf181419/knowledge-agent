"""
Database layer for KnowledgeAgent.
"""

from app.db.models import Extraction, NovelExtraction, ScrapeMetric, Trace
from app.db.session import get_engine, get_session, get_session_context, init_db

__all__ = [
    "Extraction",
    "NovelExtraction",
    "ScrapeMetric",
    "Trace",
    "get_engine",
    "init_db",
    "get_session",
    "get_session_context",
]
