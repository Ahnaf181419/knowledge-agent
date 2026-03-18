"""
Trace service for observability.
"""

import time
import uuid
from contextlib import contextmanager
from datetime import datetime

from app.db import Trace, get_session_context


class TraceService:
    """Service for adding observability traces."""

    def _ensure_tables(self):
        from app.db import init_db

        init_db()

    def __init__(self):
        self._ensure_tables()
        self._current_trace_id: str | None = None

    def start_trace(self) -> str:
        """Start a new trace and return trace_id."""
        self._current_trace_id = str(uuid.uuid4())
        return self._current_trace_id

    def get_current_trace_id(self) -> str | None:
        return self._current_trace_id

    def add_span(
        self,
        trace_id: str,
        span: str,
        event: str | None = None,
        duration_ms: int | None = None,
        metadata: dict | None = None,
    ):
        """Add a trace span."""
        with get_session_context() as session:
            trace = Trace(
                trace_id=trace_id,
                span=span,
                event=event or "span",
                trace_metadata=metadata,
                duration_ms=duration_ms,
                created_at=datetime.now(),
            )
            session.add(trace)
            session.commit()

    @contextmanager
    def trace(self, span: str, event: str | None = None):
        """Context manager for tracing."""
        trace_id = self.get_current_trace_id() or self.start_trace()
        start_time = time.perf_counter()

        try:
            yield trace_id
        finally:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self.add_span(trace_id, span, event if event is not None else span, duration_ms)

    def get_traces(self, trace_id: str) -> list:
        """Get all spans for a trace."""
        from sqlmodel import desc, select

        with get_session_context() as session:
            stmt = select(Trace).where(Trace.trace_id == trace_id).order_by(desc(Trace.created_at))
            traces = session.exec(stmt).all()
            return [
                {
                    "span": t.span,
                    "event": t.event,
                    "duration_ms": t.duration_ms,
                    "metadata": t.trace_metadata,
                    "created_at": t.created_at.isoformat(),
                }
                for t in traces
            ]


trace_service = TraceService()
