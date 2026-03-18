# KnowledgeAgent Documentation

Welcome to the KnowledgeAgent documentation.

## Quick Links

- [Architecture](./ARCHITECTURE.md)
- [API Reference](./API.md)
- [Contributing Guide](./CONTRIBUTING.md)

## Table of Contents

1. [Getting Started](#getting-started)
2. [Features](#features)
3. [Configuration](#configuration)
4. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

```bash
cd knowledge-agent
uv pip install -r requirements.txt
playwright install
cp .env.example .env
```

### Running the Application

```bash
python -m app.main_gradio
```

Open http://localhost:7860 in your browser.

## Features

### Web Scraping
- 5 scraping methods with priority-based fallback:
  - SimpleHTTP (priority 1) - requests + trafilatura
  - Playwright (priority 2) - headless browser
  - Playwright Alt (priority 3) - alternate UA
  - Playwright TLS (priority 4) - TLS fingerprinting
  - CloudScraper (priority 5) - Cloudflare bypass
- Automatic method selection via router
- Hybrid duplicate detection (SHA256 + BM25)
- Background job scheduling
- System notifications

### Queue Management
- Add URLs and novels
- Track scraping progress
- Retry failed items

### Analytics
- Method performance tracking
- Success rate analysis
- Domain-specific statistics

### Standardized Output
- YAML frontmatter metadata
- Content type detection (wiki, novel, blog)
- Auto-extracted tags

## Configuration

See [Settings](./SETTINGS.md) for configuration options.

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues.
