"""
Database models using SQLModel.
"""

from datetime import datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Extraction(SQLModel, table=True):
    """Replaces history.json - tracks all successfully extracted URLs."""

    __tablename__ = "extractions"

    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(unique=True, index=True)
    file_path: str
    word_count: int
    scraper: str
    content_type: str = Field(default="article")
    extracted_at: datetime = Field(default_factory=datetime.now)


class NovelExtraction(SQLModel, table=True):
    """Tracks novel extraction metadata."""

    __tablename__ = "novel_extractions"

    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(unique=True, index=True)
    folder: str
    name: str
    author: str = "Unknown"
    total_words: int = 0
    first_extracted: datetime = Field(default_factory=datetime.now)
    last_extracted: datetime | None = None


class ScrapeMetric(SQLModel, table=True):
    """Replaces scraping_stats.json - tracks method performance."""

    __tablename__ = "scrape_metrics"

    id: int | None = Field(default=None, primary_key=True)
    url: str
    domain: str = Field(index=True)
    method: str = Field(index=True)
    success: bool
    time_ms: int
    word_count: int = 0
    error_message: str | None = None
    scraped_at: datetime = Field(default_factory=datetime.now)


class Trace(SQLModel, table=True):
    """Observability traces for debugging."""

    __tablename__ = "traces"

    id: int | None = Field(default=None, primary_key=True)
    trace_id: str = Field(index=True)
    span: str
    event: str
    duration_ms: int | None = None
    trace_metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
