# Changelog

All notable changes to this project will be documented in this file.

## [0.0.3] - 2026-03-18

### Major Refactoring: Scraper Module

#### New Core Modules (`scraper/core/`)
Created 8 new modules for shared scraping functionality:
| Module | Purpose |
|--------|---------|
| `page_extractor.py` | Shared XPath extraction logic |
| `engine_registry.py` | Engine registration + fallback chains |
| `fallback_chain.py` | Auto-fallback execution with timing |
| `session_manager.py` | Cookie/session handling |
| `metadata_extractor.py` | Genre/tags/author extraction |
| `captcha_detector.py` | CAPTCHA detection |
| `text_cleaner.py` | Text cleaning utilities |
| `__init__.py` | Package exports |

#### Engine Refactoring
- **SimpleHTTPEngine** - Fixed to inherit from BaseEngine (added `name` and `priority` properties)
- **Playwright Engines** - All 3 engines now use shared `PageExtractor` for XPath extraction:
  - `playwright_engine.py`
  - `playwright_alt_engine.py`
  - `playwright_tls_engine.py`

#### Runner Rework
- Complete rewrite of `scraper/runner.py` to use new orchestration
- Unified 5-engine fallback chain: SimpleHTTP → Playwright → PlaywrightAlt → PlaywrightTLS → CloudScraper
- Added timing metrics for extraction

#### Cleanup
- **Deleted** `scraper/novel_scraper.py` - Dead code (never imported), useful logic moved to core/

#### Bug Fixes
- Fixed circular import issues in `app/services/background_job_service.py` and `app/services/queue_service.py` (lazy imports)
- Fixed type annotations in multiple core modules

#### Testing
- 218 unit tests - All passing
- Added new test files:
  - `tests/unit/test_engine_registry.py`
  - `tests/unit/test_fallback_chain.py`
  - `tests/unit/test_page_extractor.py`
  - `tests/unit/test_text_cleaner.py`
  - `tests/unit/test_captcha_detector.py`
  - `tests/unit/test_session_manager.py` (11 tests)
  - `tests/unit/test_metadata_extractor.py` (10 tests)

---

## [0.0.2] - 2026-03-07

### Major Changes

#### UI Migration: Streamlit → Gradio
- Complete UI rewrite using Gradio 6
- New tab-based navigation: Dashboard, Add Links, Queue, Results, Analytics, Settings
- Modern theme with customizable colors

#### Removed WebScrapingAPI (Paid)
- Replaced with 5 free scraping engines
- Removed `webscrapingapi` dependency from requirements.txt and pyproject.toml
- Removed `scraper/engines/webscrapingapi_engine.py`

#### New 5 Scraping Engines (All Free)
| Engine | Status | Description |
|--------|--------|-------------|
| SimpleHTTP | Stable | requests + trafilatura |
| Playwright | Stable | Headless browser |
| Playwright Alt | Stable | Alternative UA/viewport |
| Playwright TLS | Experimental | TLS fingerprinting |
| CloudScraper | Experimental | Cloudflare bypass |

### Architecture Changes

#### Database Layer (SQLModel)
- Added `app/db/models.py` - SQLModel definitions
- Added `app/db/session.py` - DB session management
- Migration from JSON to SQLite for history/stats

#### Services Refactoring
- Created `app/services/` module
- `history_service.py` - SQLite-backed history tracking
- `stats_service.py` - SQLite-backed statistics
- `lint_service.py` - Markdown linting (mdformat + markdownlint)

#### Removed Deprecated Files
- `app/history.py` → Use `app.services.history_service`
- `app/scraping_stats.py` → Use `app.services.stats_service`
- `app/api_tracker.py` → Removed (was for paid API)
- `app/components/` → Removed (Streamlit components)
- `app/pages/` → Removed (Streamlit pages)
- `app/styles.py` → Removed (Streamlit styles)

### New Features

#### BM25 Duplicate Detection
- Added `scraper/bm25_ranker.py`
- Hybrid approach: SHA256 + BM25 similarity
- Configurable threshold (default: 0.8)

#### Markdown Linting
- Added `app/services/lint_service.py`
- Uses mdformat (auto-fix) + markdownlint (report)
- Batch linting for output folder
- Optional auto-lint on startup

### Bug Fixes

#### Import Fixes
- Fixed broken imports in `app/ui/pages/dashboard.py`
- Fixed broken imports in `app/ui/pages/analytics.py`
- Changed from `app.scraping_stats` to `app.services.stats_service`

#### Stats Service
- Fixed duplicate `get_method_stats` method (renamed to `get_method_domain_stats`)
- Updated METHODS list: removed webscrapingapi, added cloudscraper, playwright_tls
- Fixed method labels in UI

### Documentation Updates
- Updated README.md for v0.0.3
- Updated docs/ARCHITECTURE.md
- Updated docs/API.md
- Updated PLAN.md with completion status

### Dependencies Updated

#### Removed
- streamlit
- webscrapingapi
- streamlit-shadcn-ui
- streamlit-extras

#### Added
- gradio>=4.0
- sqlmodel
- cloudscraper>=1.2
- mdformat>=0.7
- mdformat-gfm>=0.1
- mdformat-frontmatter>=0.2
- rank-bm25>=0.2

---

## [1.x] - Previous Versions

See git history for v1.x changelog.
