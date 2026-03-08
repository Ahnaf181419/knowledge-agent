# Changelog

All notable changes to this project will be documented in this file.

## [Released v0.0.2]

### Architecture Refactoring 

**BREAKING CHANGES:**
- Replaced singleton pattern with Dependency Injection (DI) container
- Old singleton files deprecated: `app/state.py`, `app/scraping_stats.py`, `app/history.py`

#### New Architecture
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│    Pages    │────→│   Services   │────→│    Repos    │
│  (Streamlit)│     │  (Business)  │     │  (Data)     │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │  Container  │
                    │  (DI Root)  │
                    └─────────────┘
```

#### New Files
| Path | Description |
|------|-------------|
| `app/container.py` | DI container with lazy-loaded singletons |
| `app/repositories/__init__.py` | Repository package exports |
| `app/repositories/interfaces.py` | Abstract base classes (ABC) |
| `app/repositories/state_repo.py` | StateRepository, StatsRepository, HistoryRepository |
| `app/services/__init__.py` | Service package exports |
| `app/services/scraping_service.py` | URL scraping orchestration |
| `app/services/analytics_service.py` | Stats aggregation |
| `app/services/novel_service.py` | Novel scraping orchestration |
| `scraper/engines/base_engine.py` | BaseScraperEngine + EngineFactory |
| `tests/conftest.py` | Pytest fixtures |
| `tests/test_repositories.py` | Repository unit tests |
| `tests/test_services.py` | Service unit tests |
| `tests/test_engines.py` | Engine unit tests |

#### Dataclasses (Type-Safe Transfer Objects)
| Class | Fields |
|-------|--------|
| `URLRecord` | url, type, status, tags, added_at, completed_at |
| `NovelRecord` | url, start_chapter, end_chapter, status, added_at |
| `RetryRecord` | url, chapter, error, tags, added_at |
| `ScrapeResult` | url, method, success, time_ms, word_count, domain |
| `ExtractionRecord` | url, file_path, word_count, method, extracted_at |

#### Deprecated Files (Keep for Reference)
- `app/state.py` → `app/repositories/state_repo.py:StateRepository`
- `app/scraping_stats.py` → `app/repositories/state_repo.py:StatsRepository`
- `app/history.py` → `app/repositories/state_repo.py:HistoryRepository`

#### Data Files (Backward Compatible)
| File | Used By |
|------|---------|
| `settings.json` | StateRepository (user preferences) |
| `queue.json` | StateRepository (URL/novel queue) |
| `scraping_stats.json` | StatsRepository (scraping statistics) |
| `history.json` | HistoryRepository (extraction tracking) |
| `api_usage.json` | API tracker module |

#### Key Improvements
1. **Connection Pooling**: `BaseScraperEngine` shares `requests.Session` across all engines
2. **Testability**: All repos implement interfaces, easy to mock in tests
3. **Type Safety**: Dataclasses replace dict returns
4. **Lazy Loading**: Container uses `@cached_property` for singletons
5. **Backward Compatible**: Uses existing JSON files (`settings.json`, `queue.json`)

#### Test Coverage
- 35 unit tests passing
- Repository tests: 17
- Service tests: 6
- Engine tests: 11

#### Bug Fixes (Post-Refactoring)
- Fixed `AttributeError: 'ScrapeResult' object has no attribute 'get'` in analytics.py
  - Changed `item.get('success')` → `item.success` (dataclass attribute access)
- Fixed `AttributeError: module 'streamlit' has no attribute 'session_container'`
  - Changed `st.session_container` → `st.session_state` (typo)
- Fixed `st.session_state.state_repo.get()` incorrect usage
  - Changed to `st.session_state.get()` for session state access
- Added `reset_settings()` method to `IStateRepository` interface and `StateRepository` implementation
  - Replaces direct access to private `_settings` and `_default_settings()` methods

---

## [Unreleased]

### Added
- Initial project setup
- Streamlit dashboard with dark/light theme
- Two input types: Normal links + Novel links with chapter range
- Smart routing with fallback priority: Simple HTTP → Playwright → WebScrapingAPI
- Trafilatura text extraction with MD/TXT/JSON export
- Queue persistence with auto-save
- Settings persistence (JSON)
- Extraction history tracking (`history.json`)
- Duplicate prevention for URLs and novels
- Novel metadata extraction (genre, tags, author)
- Retry queue for failed normal links and novel chapters
- Context manager pattern for NovelScraper (`with` statement)
- Grafana-style dashboard with tab navigation
- Scraping statistics module (`scraping_stats.json`)
- Method tracking for each scraped URL (simple_http, playwright, webscrapingapi)
- Timing data for each extraction (milliseconds)

### Dashboard Components
- Stat cards with trend indicators
- Semi-circle gauges for API usage and success rate (Plotly)
- Pie chart for method distribution
- Timeline chart for daily activity
- Bar chart for top domains
- Recent activity list with method badges
- API usage card (WebScrapingAPI style)
- Refresh button for manual data reload
- Status icons (✓/✗) for success/failure indicators

### Fixed
- Fixed module import path for Streamlit compatibility
- Fixed duplicate navigation key error in Streamlit
- Updated WebScrapingAPI to v2 with proper URL encoding
- Fixed scraping functionality - Start button now actually runs scraper
- Added scraper runner module for execution
- Fixed UTF-8 encoding issues on Windows (logger, Crawl4AI output)
- Fixed concurrent scraping causing Playwright async conflicts
- Fixed text extraction - Crawl4AI returns markdown directly
- Fixed arrow character encoding issues in UI
- Fixed tags having trailing commas (e.g., `"Male Protagonist,"` → `"Male Protagonist"`)
- Fixed title showing "None" string when extraction fails
- Fixed novel chapter retry missing genre/tags metadata
- Fixed Playwright browser resource leak on exceptions
- Fixed WebScrapingAPI call counter being incremented twice
- Fixed URL routing - pages now work via tab navigation
- Fixed blank page issue when navigating
- Fixed navigation tabs showing raw variable names

### UI Improvements
- Complete redesign with Grafana dark theme
- Tab-based top navigation (replaced sidebar)
- Real-time progress bar during scraping
- Chapter-by-chapter progress for novels
- Toast notifications for user actions
- Panel-based layout with borders
- Color-coded method badges (SimpleHTTP=blue, Playwright=purple, API=orange)
- Clean stat cards without misleading zeros
- Success rate calculation and display
- Batch retry operations ("Retry All", "Clear All" buttons)
- Progress bar during batch API retry

### Features
- URL validation before scraping
- Real-time progress tracking
- Export: Markdown (default), TXT, JSON
- Novel chapter auto-resume (skip existing)
- Organized folder structure by domain/type
- Sequential or concurrent URL processing
- Novel scraper with Playwright + Playwright-alt fallback
- Configurable delay between novel chapters
- Session cookie management for novels
- XPath-based text extraction for novels
- Method tracking with fallback chain logging
- Extraction time measurement (ms)
- Daily activity statistics

### API Tracking
- Monthly call limit: 5,000 calls
- Warning at 4,500 calls (90%)
- Auto-stop at 4,998 calls (99.96%)
- Monthly reset on 1st of each month
- Prominent API usage card in dashboard

### Settings (All 9 Functional)
| Setting | Description | Implementation |
|---------|-------------|----------------|
| `theme` | Dark/Light theme | main.py |
| `export_format` | MD/TXT/JSON | runner.py |
| `output_folder` | Output directory | folder_manager.py |
| `concurrent_jobs` | Parallel scraping | runner.py (ThreadPoolExecutor) |
| `retry_count` | Retries per method | runner.py, novel_scraper.py |
| `novel_delay_min` | Min delay between chapters | novel_scraper.py |
| `novel_delay_max` | Max delay between chapters | novel_scraper.py |
| `auto_save_queue` | Auto-save on changes | state.py |
| `respect_robots_txt` | Check robots.txt | runner.py (robots_checker.py) |

### Security
- API key moved from `config.py` to `.env` file
- `.env` added to `.gitignore`
- `.env.example` template provided for new users
- API key saving in Settings page writes to `.env`

### Code Cleanup
- Removed `pages_routes/` directory (5 files, ~100 lines)
- Removed `app/components/sidebar.py` (~97 lines)
- Fixed router naming: `crawl4ai` → `simple_http`
- Removed duplicate `novel_delay` key from settings.json

### Dependencies
- streamlit >= 1.28
- plotly >= 5.18.0 (charts and gauges)
- pandas >= 2.0.0 (data aggregation)
- trafilatura >= 2.0
- playwright
- playwright-stealth
- requests
- python-dotenv (environment variables)
- streamlit-shadcn-ui (UI components)
- streamlit-extras (stylable containers)

## Scraping Strategy

### Normal Links (4-Step)
```
Step 1: Simple HTTP + Trafilatura     → Fast, lightweight
Step 2: Playwright + XPath            → JS rendering fallback
Step 3: Playwright Alt Config         → Different UA/viewport
Step 4: FAILED → Retry Table          → User chooses: WebScrapingAPI or Remove
```

### Novel Links (2-Step + Retry)
```
Step 1: Playwright stealth            → Headless, stealth_sync
Step 2: Playwright alt config         → Different UA/viewport
Step 3: FAILED → Retry Table          → User chooses: WebScrapingAPI or Remove
```

## [Planned]
- RAG integration (separate agent)
- Search functionality across scraped content
- React + FastAPI migration (optional)

---

## 2026-02-21

### Analytics Tab
- **New Analytics Tab** - Comprehensive scraping method statistics (6th position, before Settings)
- Time period filtering: All Time, 7/15/30/90/180/365 days (select_slider)
- Method comparison radar/spider chart (success_rate, speed_score, efficiency)
- Efficiency scoring formula: `(success_rate * 0.4) + (speed_score * 0.3) + (word_score * 0.3)`
- Stacked area chart for method usage over time
- Success/fail ratio grouped bar chart by method
- Average extraction time comparison chart
- Domain analysis with success/fail breakdown
- Error distribution pie chart
- Recent activity list with detailed metrics
- Efficiency rankings table with medals (🥇🥈🥉)

### Method Tracking (4 Methods)
- `simple_http` - Simple HTTP + Trafilatura
- `playwright` - Headless browser with stealth
- `playwright_alt` - Alternative browser config
- `webscrapingapi` - Third-party API

### Bug Fixes
- **API counter bug**: `increment_api_calls()` now only called on successful 200 response
- **Error message truncation**: `...` suffix only added when string exceeds limit
- **None handling**: Error messages use `or 'Unknown'` for safety

### Code Cleanup
- Deleted `app/components/progress.py` (unused)
- Deleted `app/components/panels.py` (unused)
- Deleted `app/components/charts.py` (redundant)

### UI Theme Improvements
- **Dark Theme**: Softer, more readable colors
  - Background: `#1a1a2e` (soft dark blue) instead of `#0b0b0b` (pure black)
  - Text: `#e8eaed` (off-white), `#a8b2c1` (secondary)
  - Accent: `#5c9eff` (softer blue)
  - Success/Warning/Error: `#4ade80`, `#fbbf24`, `#f87171`
  
- **Light Theme**: Cleaner, softer palette
  - Background: `#f8fafc` (softer white)
  - Text: `#1e293b` (dark slate), `#64748b` (secondary)
  - Accent: `#3b82f6` (clean blue)

- **Charts**: Updated all colors for better readability

### Files Modified
| File | Change |
|------|--------|
| `app/pages/analytics.py` | New Analytics page |
| `app/scraping_stats.py` | Rewritten with 4-method support |
| `app/components/analytics_charts.py` | New chart functions |
| `app/components/gauges.py` | Updated colors |
| `app/styles.py` | Complete theme overhaul |
| `app/main.py` | Added Analytics tab |
| `app/pages/dashboard.py` | Simplified to overview |
| `scraper/runner.py` | Added playwright_alt fallback |
| `scraper/novel_scraper.py` | Added stats recording |
| `app/components/__init__.py` | Updated exports |
