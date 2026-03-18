# KnowledgeAgent v0.0.3

A web scraping tool for building personal knowledge bases. Extract articles, blogs, wikis, and novels into clean Markdown files ready for RAG applications.

## Quick Start

```bash
cd knowledge-agent
pip install -r requirements.txt
playwright install
python -m app.main
```

Open http://localhost:7860

## Features

### Input Types
| Type | Description | Example |
|------|-------------|---------|
| Normal links | Single URLs | Wikipedia, blogs, articles |
| Novel links | Chapter range | wtr-lab.com novels |

### 5 Scraping Engines (All Free)

| Engine | Use Case | Status |
|--------|----------|--------|
| SimpleHTTP | Static pages | Stable |
| Playwright | JS-heavy pages | Stable |
| Playwright Alt | Alternative browser config | Stable |
| Playwright TLS | TLS fingerprinting | Experimental |
| CloudScraper | Cloudflare bypass | Experimental |

### UI (Gradio)
- Tab-based navigation
- Dashboard with stats
- Queue management
- Results viewer
- Analytics with method performance
- Settings configuration

### Navigation

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
│   ├── main.py              # Gradio entry point
│   ├── config.py            # Configuration loading
│   ├── state.py             # Queue & settings management
│   ├── db/                  # SQLite database layer
│   │   ├── models.py        # SQLModel definitions
│   │   └── session.py       # DB session management
│   ├── services/            # Business logic
│   │   ├── scraper_service.py
│   │   ├── history_service.py
│   │   ├── stats_service.py
│   │   ├── lint_service.py
│   │   └── ...
│   └── ui/                  # Gradio UI
│       ├── components/
│       └── pages/
├── scraper/
│   ├── router.py            # URL routing
│   ├── runner.py            # Scraping execution
│   ├── core/                # Shared scraping utilities
│   │   ├── page_extractor.py
│   │   ├── engine_registry.py
│   │   ├── fallback_chain.py
│   │   ├── session_manager.py
│   │   ├── metadata_extractor.py
│   │   ├── captcha_detector.py
│   │   └── text_cleaner.py
│   ├── bm25_ranker.py       # BM25 duplicate detection
│   └── engines/             # 5 scraping engines
│       ├── simple_http_engine.py
│       ├── playwright_engine.py
│       ├── playwright_alt_engine.py
│       ├── playwright_tls_engine.py
│       └── cloudscraper_engine.py
├── storage/
│   ├── folder_manager.py
│   └── markdown_saver.py
├── utils/
│   ├── validators.py
│   ├── robots_checker.py
│   └── content_hasher.py
├── output/                  # Scraped content
├── requirements.txt
└── settings.json
```

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `theme` | dark | Dark/Light theme toggle |
| `export_format` | md | Output format (md/txt/json) |
| `output_folder` | output | Directory for scraped files |
| `concurrent_jobs` | 2 | Parallel URL processing |
| `retry_count` | 2 | Retries per scraping method |
| `novel_delay_min` | 90 | Min delay between chapters (seconds) |
| `novel_delay_max` | 120 | Max delay between chapters (seconds) |
| `auto_save_queue` | true | Auto-save queue on changes |
| `respect_robots_txt` | true | Check robots.txt before scraping |

## Output Format (v2.0)

```yaml
---
title: "Page Title"
source_url: "https://example.com/article"
scraped_at: "2026-03-07T10:30:00Z"
engine: "playwright"
content_type: "wiki"  # wiki | novel | blog | article
tags: []
word_count: 5551
---

# Page Title

[Content...]
```

## Dependencies

```
gradio>=4.0
sqlmodel
trafilatura>=2.0
playwright
playwright-stealth
cloudscraper>=1.2
requests
plotly>=5.18.0
pandas>=2.0.0
mdformat>=0.7
rank-bm25>=0.2
```

## License

MIT
