# Testing Guide

## Overview

This document covers the testing infrastructure, patterns, and known issues for the web scraping application.

## Test Commands

### Running Tests

```bash
# Run all unit tests
python -m pytest tests/unit -v

# Run all integration tests
python -m pytest tests/integration/test_services_integration.py -v

# Run all tests
python -m pytest tests/integration tests/unit -v
```

### Code Quality

```bash
# Linting and formatting with ruff
ruff check .
ruff format .

# Type checking with mypy
mypy .
```

### Verify Imports

```bash
python -c "from app.services import *; from scraper.router import route_url; print('All imports OK')"
```

## Test Structure

- **Unit Tests** (`tests/unit/`): 152 tests covering individual components
- **Integration Tests** (`tests/integration/`): 22 tests covering service interactions
- **Total**: 174 tests passing

## Known Issues & Fixes

### Integration Test API Corrections

The integration tests had several API mismatches that were fixed:

1. **`StatsService` and `HistoryService`**: Don't take `enabled` parameter in constructor
2. **`RetryService`**: 
   - `get_retry_queue()` doesn't exist - use `get_retry_items()`
   - `add_to_retry_queue()`, `should_retry()`, `record_retry_attempt()` don't exist
3. **`get_domain_stats()`**: Returns `list[dict]` not a dict with `.get()` method
4. **`get_summary()`**: Doesn't exist - use `get_summary_stats()`
5. **`route_url()`**: Returns `str` (Literal type) not an object with `.method` attribute
6. **Novel URLs**: Need `/novel/` path, not `/reader/` to be detected

### SQLModel API

In `app/services/stats_service.py`:
- Use `.one()` instead of `.scalar()` for aggregate queries

### Method Optimizer

In `scraper/method_optimizer.py`:
- Use `get_method_domain_stats(domain, method)` instead of `get_method_stats(domain, method)`

## Files Modified

| File | Changes |
|------|---------|
| `tests/integration/test_services_integration.py` | Fixed API calls: removed `enabled=True` params, fixed `RetryService` method calls, fixed `get_summary` → `get_summary_stats`, fixed router test URLs, fixed stats assertions |
| `tests/unit/test_method_optimizer.py` | Fixed mock method names: `get_method_stats` → `get_method_domain_stats` |
| `app/services/stats_service.py` | Fixed SQLModel API: `.scalar()` → `.one()` on line 214 |
| `scraper/method_optimizer.py` | Fixed API call: `get_method_stats(domain, method)` → `get_method_domain_stats(domain, method)` on line 78 |

---

## v2 Cleanup

Removed obsolete files from v1 (Streamlit → Gradio migration):

### Deleted
| Path | Reason |
|------|--------|
| `.streamlit/` | Streamlit config (replaced by Gradio) |
| `history.json` | Old v1 format (now uses SQLite) |
| `queue.json` | Old v1 format (now uses `state.queue`) |
| `scraping_stats.json` | Contained old webscrapingapi references |
| `logs/scraper_20260220.log` | Old v1 logs |
| `logs/scraper_20260221.log` | Old v1 logs |
| `-p/` | Empty artifact directory |
