# API Reference

## Core Modules

### app.state

```python
from app.state import state

# Settings
state.get_setting(key: str, default: Any) -> Any
state.set_setting(key: str, value: Any) -> None
state.save_settings() -> None

# Queue management
state.add_url(url: str, url_type: str = "normal", tags: list = None) -> bool
state.add_novel(url: str, start_chapter: int, end_chapter: int) -> bool
state.remove_url(url: str) -> None
state.remove_novel(url: str) -> None
state.update_url_status(url: str, status: str, error: str = None) -> None
state.clear_completed() -> None

# Retry queue
state.add_to_retry_normal(url: str, error: str, tags: list = None) -> None
state.add_to_retry_novel(url: str, chapter: int, error: str) -> None
state.get_retry_normal() -> list
state.get_retry_novel() -> list
```

### app.db.models (SQLite via SQLModel)

```python
from app.db.models import Extraction, ScrapeMetric, Trace
from app.db.session import get_session

# Extraction - tracks scraped URLs
extraction = Extraction(
    url="https://example.com",
    file_path="output/example.md",
    word_count=1000,
    scraper="playwright",
    content_type="wiki",
    tags=["topic"],
    source_url="https://example.com"
)

# ScrapeMetric - performance metrics
metric = ScrapeMetric(
    url="https://example.com",
    domain="example.com",
    method="playwright",
    success=True,
    time_ms=1500,
    word_count=1000
)

# Trace - observability
trace = Trace(
    trace_id="abc123",
    span="scrape",
    event="start",
    duration_ms=1500
)

# Database session
with get_session() as session:
    session.add(extraction)
    session.commit()
```

### scraper.router

```python
from scraper.router import route_url, get_route_reason

# URL routing
route_url(url: str) -> RouterResult  # "skip" | "novel" | "simple_http" | "heavy"
get_route_reason(url: str) -> str
```

### scraper.runner

```python
from scraper.runner import ScraperRunner, run_scraper

# Usage
runner = ScraperRunner()
results = runner.run(urls: list) -> list

# Single URL
result = runner.scrape_normal_url(url: str, tags: list) -> dict
```

### scraper.core

```python
from scraper.core import (
    PageExtractor,
    EngineRegistry,
    FallbackChain,
    SessionManager,
    MetadataExtractor,
    CaptchaDetector,
    TextCleaner
)

# Page extraction with XPath
extractor = PageExtractor()
content = extractor.extract(html: str, xpaths: dict) -> dict

# Engine registry and fallback
registry = EngineRegistry()
registry.register(engine)
chain = registry.get_fallback_chain()
result = chain.execute(url: str) -> ScrapingResult

# Session management
session_mgr = SessionManager()
session_mgr.set_cookies(url, cookies)
cookies = session_mgr.get_cookies(url)

# Metadata extraction
metadata = MetadataExtractor.extract(html: str, url: str) -> dict

# CAPTCHA detection
is_captcha = CaptchaDetector.detect(html: str, url: str) -> bool

# Text cleaning
cleaned = TextCleaner.clean(html: str) -> str
```

### scraper.engines

```python
from scraper.engines import (
    SimpleHTTPEngine,
    PlaywrightEngine,
    PlaywrightAltEngine,
    PlaywrightTLSEngine,
    CloudScraperEngine
)

# All engines implement the same interface
engine = SimpleHTTPEngine()
html_content = engine.scrape(url: str) -> str | None

# Engine priorities (lower = higher priority)
# SimpleHTTPEngine: priority=1
# PlaywrightEngine: priority=2
# PlaywrightAltEngine: priority=3
# PlaywrightTLSEngine: priority=4
# CloudScraperEngine: priority=5
```

### app.services.lint_service

```python
from app.services.lint_service import LintService, LintResult

lint_service = LintService(output_folder="output")

# Lint a single file
result: LintResult = lint_service.lint_file("output/example.md", fix=True)

# Lint entire output folder
results: list[LintResult] = lint_service.lint_output_folder(fix=True)

# Get summary
summary = lint_service.get_status_summary(results)
# Returns: {"total": N, "fixed": N, "success": N, "issues": N, "errors": N, "skipped": N}
```

### scraper.bm25_ranker

```python
from scraper.bm25_ranker import BM25Ranker

ranker = BM25Ranker()
ranker.add_document(doc_id: str, content: str) -> None
scores = ranker.get_scores(query: str) -> list[float]
is_duplicate = ranker.is_duplicate(content: str, threshold: float = 0.8) -> bool
ranker.clear() -> None
```

### storage.markdown_saver

```python
from storage.markdown_saver import MarkdownSaver

saver = MarkdownSaver()
saver.save(
    content="...",
    file_path="output/example.md",
    metadata={
        "title": "Example",
        "source_url": "https://example.com",
        "engine": "playwright",
        "content_type": "wiki",
        "tags": ["topic"],
        "word_count": 1000
    }
)
```

### utils.validators

```python
from utils.validators import (
    is_valid_url,
    is_youtube_url,
    is_novel_url,
    get_domain,
    generate_slug,
    check_url_reachable,
    validate_chapter_range,
    parse_tags
)
```

### utils.content_hasher

```python
from utils.content_hasher import hash_content, hash_url

content_hash = hash_content(content: str) -> str
url_hash = hash_url(url: str) -> str
```

## Data Structures

### ScrapeResult

```python
class ScrapeResult(TypedDict):
    url: str
    status: "pending" | "processing" | "completed" | "failed" | "skipped"
    method: str | None
    fallback_chain: list[str]
    extraction_time_ms: int
    word_count: int
    error: str | None
    file_path: str | None
```

### QueueEntry

```python
class QueueEntry(TypedDict):
    url: str
    type: "normal" | "novel"
    tags: list[str]
    status: str
    error: str | None
    added_at: str  # ISO timestamp
```

### MarkdownMetadata (v2.0)

```python
class MarkdownMetadata(TypedDict):
    title: str
    source_url: str
    scraped_at: str  # ISO 8601
    engine: str
    content_type: str  # wiki | novel | blog | article
    tags: list[str]
    word_count: int
    # Optional - novel
    chapter: int | None
    chapter_title: str | None
    novel: str | None
    author: str | None
    previous_url: str | None
    next_url: str | None
    # Optional - wiki
    sections: list[str] | None
    related_urls: list[str] | None
    # Optional - blog
    published_date: str | None
```

### Settings

```python
class Settings(TypedDict):
    theme: "dark" | "light"
    export_format: "md" | "txt" | "json"
    output_folder: str
    concurrent_jobs: int
    retry_count: int
    novel_delay_min: int
    novel_delay_max: int
    auto_save_queue: bool
    respect_robots_txt: bool
    notifications_enabled: bool
    auto_optimize: bool
    optimization_threshold: int
    success_promotion_threshold: int
    bm25_similarity_threshold: float
```

## Events

### Scraper Events

- `on_scraper_start`: Called when scraping begins
- `on_scraper_complete`: Called when scraping completes
- `on_scraper_error`: Called when scraping fails
- `on_method_fallback`: Called when method falls back

### Queue Events

- `on_url_added`: Called when URL added to queue
- `on_url_removed`: Called when URL removed from queue
- `on_status_change`: Called when URL status changes
