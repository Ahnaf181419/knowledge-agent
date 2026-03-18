# Settings Reference

## Application Settings

All settings are stored in `settings.json` and can be modified through the Settings page in the application.

### General Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `theme` | string | `"dark"` | UI theme: `"dark"` or `"light"` |
| `export_format` | string | `"md"` | Output format: `"md"`, `"txt"`, or `"json"` |
| `output_folder` | string | `"output"` | Directory for scraped files |

### Scraping Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `concurrent_jobs` | int | `2` | Maximum parallel scraping jobs (1-3) |
| `retry_count` | int | `2` | Number of retries per scraping method |
| `respect_robots_txt` | bool | `true` | Check robots.txt before scraping |

### Novel Scraping Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `novel_delay_min` | int | `90` | Minimum delay between chapters (seconds) |
| `novel_delay_max` | int | `120` | Maximum delay between chapters (seconds) |

### Queue Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `auto_save_queue` | bool | `true` | Automatically save queue on changes |

### Notification Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `notifications_enabled` | bool | `true` | Enable system notifications |

### Optimization Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `auto_optimize` | bool | `true` | Enable automatic method optimization |
| `optimization_threshold` | int | `50` | Run optimization after this many scrapes |
| `success_promotion_threshold` | int | `5` | Success count to promote a method |
| `bm25_similarity_threshold` | float | `0.8` | Similarity threshold for duplicate detection |

## Environment Variables

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `"INFO"` | Logging level: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"` |
| `OUTPUT_FOLDER` | `"output"` | Override output directory |

## File Locations

| File | Description |
|------|-------------|
| `settings.json` | User settings |
| `queue.json` | Pending URLs and novels |
| `knowledge.db` | SQLite database (history, metrics, traces) |
| `output/` | Scraped markdown files |
| `logs/scraper_*.log` | Application logs |

## Configuration via Code

### Reading Settings

```python
from app.state import state

# Get a setting
theme = state.get_setting('theme', 'dark')

# Get all settings
all_settings = state.settings
```

### Writing Settings

```python
from app.state import state

# Set a setting
state.set_setting('theme', 'light')

# Settings are automatically saved
```

### Default Settings

```python
DEFAULT_SETTINGS = {
    "theme": "dark",
    "export_format": "md",
    "output_folder": "output",
    "concurrent_jobs": 2,
    "retry_count": 2,
    "novel_delay_min": 90,
    "novel_delay_max": 120,
    "auto_save_queue": True,
    "respect_robots_txt": True,
    "notifications_enabled": True,
    "auto_optimize": True,
    "optimization_threshold": 50,
    "success_promotion_threshold": 5,
    "bm25_similarity_threshold": 0.8
}
```

## Advanced Configuration

### Custom Output Folder

```python
state.set_setting('output_folder', 'my_custom_output')
```

### Performance Tuning

For slower systems, reduce concurrent jobs:
```python
state.set_setting('concurrent_jobs', 1)
```

For faster systems with more resources:
```python
state.set_setting('concurrent_jobs', 3)
```

### Duplicate Detection Tuning

Adjust BM25 threshold for more/less strict duplicate detection:
```python
# More strict (lower threshold = more duplicates flagged)
state.set_setting('bm25_similarity_threshold', 0.7)

# Less strict (higher threshold = fewer duplicates flagged)
state.set_setting('bm25_similarity_threshold', 0.9)
```

### Optimization Control

Disable automatic optimization:
```python
state.set_setting('auto_optimize', False)
```

Adjust optimization frequency:
```python
# Run optimization every 100 scrapes
state.set_setting('optimization_threshold', 100)

# Require 10 successes to promote a method
state.set_setting('success_promotion_threshold', 10)
```
