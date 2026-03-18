# Architecture

## Overview

KnowledgeAgent uses a modular architecture with clear separation between:
- **UI Layer**: Gradio-based user interface
- **Service Layer**: Business logic services
- **Scraper Layer**: Web scraping engines
- **Storage Layer**: File and data persistence

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      UI Layer (Gradio)                     │
├─────────┬─────────┬─────────┬─────────┬─────────┬─────────┤
│Dashboard│Add Links│  Queue  │ Results │Analytics│ Settings│
└────┬────┴────┬────┴────┬────┴────┬────┴────┬────┴────┬────┘
     │         │         │         │         │         │
     └─────────┴─────────┴────┬────┴─────────┴─────────┘
                               │
┌──────────────────────────────┴──────────────────────────────┐
│                      Service Layer                           │
├──────────────┬──────────────┬──────────────┬───────────────┤
│ScraperService│Notification  │  Scheduler   │   Lint         │
│              │  Service     │   Service    │   Service     │
│              │              │              │               │
│              │              │              │               │
│              │              │              │               │
│              │              │              │               │
└──────┬───────┴──────┬───────┴──────┬───────┴───────┬────────┘
       │              │              │               │
       └──────────────┴──────────────┴───────────────┘
                                │
┌──────────────────────────────┴──────────────────────────────┐
│                      Scraper Layer                           │
├──────────────────┬───────────────────────────────────────────┤
│     Router       │              Engine Factory               │
│  (URL routing)   │         (5 Scraping Methods)             │
├──────────────────┼───────────────────────────────────────────┤
│                  │  ┌───────┬─────────┬─────────┬───────┬────┐│
│  BM25 Ranker    │  │Simple │Playwright│Alt   │TLS   │Cloud││
│  (Duplicate     │  │HTTP   │         │       │      │Scraper││
│   detection)    │  │(pri=1)│(pri=2)  │(pri=3)│(pri=4)│(pri=5)│
│                  │  └───────┴─────────┴─────────┴───────┴────┘│
└──────────────────┴───────────────────────────────────────────┘
                                │
┌──────────────────────────────┴──────────────────────────────┐
│                      Storage Layer                           │
├──────────────────┬──────────────────┬───────────────────────┤
│  Folder Manager  │ Markdown Saver   │   Database (SQLite)    │
│  (Output dirs)   │ (File writing)  │ (SQLModel ORM)         │
│                  │                  │ - Extraction history   │
│                  │                  │ - Scrape metrics       │
│                  │                  │ - Traces                │
└──────────────────┴──────────────────┴───────────────────────┘
```

## Components

### UI Layer

| Component | Description |
|-----------|-------------|
| `app/main_gradio.py` | Gradio app entry point |
| `app/ui/pages/` | Individual page implementations |
| `app/ui/components/` | Reusable UI components |

### Service Layer

| Service | Description |
|---------|-------------|
| `ScraperService` | Orchestrates scraping operations |
| `NotificationService` | System notifications |
| `SchedulerService` | Background job scheduling |
| `LintService` | Markdown linting (mdformat + markdownlint) |

### Scraper Layer

| Component | Description |
|-----------|-------------|
| `router.py` | URL routing and method selection |
| `runner.py` | Scraping execution with fallback chain |
| `core/` | Shared scraping utilities |
| `core/page_extractor.py` | Shared XPath extraction logic |
| `core/engine_registry.py` | Engine registration + fallback chains |
| `core/fallback_chain.py` | Auto-fallback execution with timing |
| `core/session_manager.py` | Cookie/session handling |
| `core/metadata_extractor.py` | Genre/tags/author extraction |
| `core/captcha_detector.py` | CAPTCHA detection |
| `core/text_cleaner.py` | Text cleaning utilities |
| `engines/` | 5 scraping engine implementations |
| `engines/base.py` | BaseEngine abstract class |
| `engines/simple_http_engine.py` | Simple HTTP + trafilatura |
| `engines/playwright_engine.py` | Playwright headless browser |
| `engines/playwright_alt_engine.py` | Playwright with alternate UA |
| `engines/playwright_tls_engine.py` | Playwright with TLS fingerprinting |
| `engines/cloudscraper_engine.py` | CloudScraper for Cloudflare bypass |
| `bm25_ranker.py` | BM25-based duplicate detection |
| `method_optimizer.py` | Self-optimization logic |

### Storage Layer

| Component | Description |
|-----------|-------------|
| `folder_manager.py` | Dynamic output directory management |
| `markdown_saver.py` | Markdown file writing with YAML frontmatter |
| `app/db/models.py` | SQLModel database models |
| `app/db/session.py` | Database session management |
| `app/state.py` | Queue and settings persistence (JSON) |

### Database Schema (SQLite via SQLModel)

| Table | Description |
|-------|-------------|
| `Extraction` | Tracks scraped URLs and file paths |
| `ScrapeMetric` | Performance metrics per scrape |
| `Trace` | Observability traces for debugging |

## Data Flow

### Scraping Flow

1. User adds URLs through UI
2. URLs validated and added to queue
3. Scheduler picks up URLs for processing
4. Router determines best scraping method
5. Runner executes scraping with fallback chain
6. Content extracted and processed
7. SHA256 hash check (exact duplicate)
8. BM25 check (similar content)
9. Content saved to output (v2.0 YAML format)
10. Stats updated in SQLite
11. Notification sent (if enabled)

### Optimization Flow

1. Each scrape records success/failure to SQLite
2. After N scrapes (configurable), optimization runs
3. Method success rates calculated per domain
4. Methods with high success promoted
5. Router uses optimized method order

## Configuration

See [Settings](./SETTINGS.md) for configuration details.

## Error Handling

- **Level 1**: Retry within same method (configurable retries)
- **Level 2**: Fallback to next method in chain
- **Level 3**: Add to retry queue
- **Level 4**: User notification with error details

## Concurrency

- Maximum 2-3 concurrent jobs (configurable)
- asyncio-based parallel execution
- Queue-based job distribution
- Resource usage monitoring
