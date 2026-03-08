# KnowledgeAgent

**Version: V0.0.2**

A web scraping tool for building personal knowledge bases. Extract articles, blogs, wikis, and novels into clean Markdown files ready for RAG applications.

## Quick Start

```bash
cd knowledge-agent
pip install -r requirements.txt
playwright install
cp .env.example .env
# Edit .env and add your WebScrapingAPI key
streamlit run app/main.py
```

Open http://localhost:8501/dashboard

## Architecture

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

### Layers
| Layer | Purpose | Files |
|-------|---------|-------|
| Pages | Streamlit UI | `app/pages/*.py` |
| Services | Business logic | `app/services/*.py` |
| Repositories | Data access | `app/repositories/*.py` |
| Container | DI composition root | `app/container.py` |

### Dependency Injection
All dependencies flow through the container:
```python
from app.container import container

# Access repositories
settings = container.state_repo.get_setting('theme')
queue = container.state_repo.queue

# Access services
result = container.scraping_service.scrape_url(url)
```

## Features

### Input Types
| Type | Description | Example |
|------|-------------|---------|
| Normal links | Single URLs | Wikipedia, blogs, articles |
| Novel links | Chapter range | novels |

### 4-Step Scraping Strategy

#### Normal Links
| Step | Method | Description |
|------|--------|-------------|
| 1 | Simple HTTP + Trafilatura | Fast, lightweight extraction |
| 2 | Playwright + XPath | JS rendering fallback |
| 3 | Playwright Alt | Different UA/viewport config |
| 4 | Retry Table → WebScrapingAPI | Manual decision |

#### Novel Links
| Step | Method | Description |
|------|--------|-------------|
| 1 | Playwright stealth | Headless with stealth_sync |
| 2 | Playwright alt config | Different UA/viewport |
| 3 | Retry Table | Manual retry queue |
| 4 | User Decision | WebScrapingAPI or Remove |

### Scraping Methods

| Method | Use Case | Speed | API Cost |
|--------|----------|-------|----------|
| SimpleHTTP | Static pages | Fast | Free |
| Playwright | JS-heavy pages | Medium | Free |
| Playwright Alt | Alternative browser config | Medium | Free |
| WebScrapingAPI | Blocked sites | Varies | 5K/month |

### Dashboard (Grafana-style)
- Tab-based top navigation
- Stat cards with trend indicators
- Semi-circle gauges for API/success rate
- Charts: pie, timeline, bar
- Real-time progress tracking
- Refresh button for manual reload
- Status icons (✓/✗) for success/failure

### Retry Table
- Batch retry all items with one click
- Clear all failed items
- Individual retry/remove buttons
- Progress bar during batch operations

### Analytics Tab
- Time period filtering (All Time, 7/15/30/90/180/365 days)
- Radar chart comparing methods (success rate, speed, efficiency)
- Efficiency rankings with formula: `40% success + 30% speed + 30% words`
- Stacked area chart for method usage over time
- Success/fail ratio by method
- Domain analysis with breakdown
- Error distribution pie chart
- Recent activity with timing data

## Navigation

| Tab | Description |
|-----|-------------|
| Dashboard | Overview and quick stats |
| Add Links | Add URLs and novels |
| Queue | Manage pending items |
| Results | View scraped files |
| Analytics | Method statistics and trends |
| Settings | Configure preferences |

## Project Structure

```
knowledge-agent/
├── app/
│   ├── main.py              # Entry point (st.tabs)
│   ├── container.py         # DI container (composition root)
│   ├── config.py            # Loads API key from .env
│   ├── api_tracker.py       # API limits (5K/month)
│   ├── logger.py            # Logging configuration
│   ├── styles.py            # Theme styles
│   ├── repositories/        # Data access layer
│   │   ├── __init__.py      # Package exports
│   │   ├── interfaces.py    # Abstract base classes (ABC)
│   │   └── state_repo.py    # StateRepository, StatsRepository, HistoryRepository
│   ├── services/            # Business logic layer
│   │   ├── __init__.py      # Package exports
│   │   ├── scraping_service.py
│   │   ├── analytics_service.py
│   │   └── novel_service.py
│   ├── components/          # UI components
│   │   ├── gauges.py        # Plotly gauges
│   │   ├── stat_cards.py    # Metric cards
│   │   ├── analytics_charts.py  # Radar, stacked, bar charts
│   │   ├── api_card.py      # API usage display
│   │   └── shadcn_helpers.py # Card containers
│   └── pages/               # Page content
│       ├── dashboard.py     # Overview (simplified)
│       ├── home.py          # Add links
│       ├── queue.py         # Queue + retry tables
│       ├── results.py       # View files
│       ├── analytics.py     # Method statistics
│       └── settings.py      # Preferences
├── scraper/
│   ├── router.py            # URL routing (simple_http/novel/webscrapingapi)
│   ├── runner.py            # ThreadPoolExecutor + 3-step fallback
│   ├── novel_scraper.py     # 2-step Playwright + stats
│   └── engines/
│       ├── base_engine.py   # BaseScraperEngine + EngineFactory
│       ├── simple_http_engine.py
│       └── webscrapingapi_engine.py
├── storage/
│   ├── folder_manager.py    # Dynamic output folder from settings
│   └── markdown_saver.py
├── utils/
│   ├── validators.py        # URL validation
│   └── robots_checker.py    # robots.txt compliance
├── tests/                   # Unit tests (35 tests)
│   ├── conftest.py          # Pytest fixtures
│   ├── test_repositories.py
│   ├── test_services.py
│   └── test_engines.py
├── output/                  # Scraped content (configurable)
├── .env                     # API key (gitignored)
├── .env.example             # Template for new users
├── history.json             # Extraction database
├── scraping_stats.json      # Statistics (4 methods tracked)
├── queue.json               # Pending items + retry queues
└── settings.json            # User preferences
```

## Settings

All 9 settings are now fully functional:

| Setting | Default | Description |
|---------|---------|-------------|
| `theme` | dark | Dark/Light theme toggle |
| `export_format` | md | Output format (md/txt/json) |
| `output_folder` | output | Directory for scraped files |
| `concurrent_jobs` | 3 | Parallel URL processing |
| `retry_count` | 2 | Retries per scraping method |
| `novel_delay_min` | 90 | Min delay between chapters (seconds) |
| `novel_delay_max` | 120 | Max delay between chapters (seconds) |
| `auto_save_queue` | true | Auto-save queue on changes |
| `respect_robots_txt` | true | Check robots.txt before scraping |

## Output Format

```
output/                          # Configurable via settings
├── wikipedia.org/
│   └── article.md
└── novels/
    └── my-novel/
        ├── chapter_1.md
        ├── chapter_2.md
        └── chapters_index.md
```

### Chapter File

```markdown
---
chapter_number: 1
title: "Chapter 1"
novel: "my-novel"
genre: ["adventure", "drama"]
tags: ["Male Protagonist"]
word_count: 1524
source: ""
scraped_at: 2024-01-15T10:30:00
---

# Chapter 1

[Content...]
```

## API Configuration

1. Copy `.env.example` to `.env`
2. Add your WebScrapingAPI key:
   ```
   WEBSCRAPING_API_KEY=your_key_here
   ```
3. Or set it via Settings page in the app

### API Limits

- **Limit:** 5,000 calls/month
- **Warning:** 4,500 (90%)
- **Stop:** 4,998 (99.96%)
- **Reset:** 1st of each month

## Dependencies

```
streamlit>=1.28
plotly>=5.18.0
pandas>=2.0.0
trafilatura>=2.0
playwright
playwright-stealth
requests
python-dotenv
streamlit-shadcn-ui
streamlit-extras
pytest>=9.0           # Testing
pytest-asyncio        # Async test support
faker                 # Test data generation
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_repositories.py -v

# Run with coverage
pytest tests/ -v --cov=app --cov=scraper
```

## License

MIT
