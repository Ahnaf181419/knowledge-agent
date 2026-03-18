# Contributing to KnowledgeAgent

Thank you for contributing to KnowledgeAgent!

## Development Setup

### Prerequisites

- Python 3.13+
- Node.js (for Playwright)
- uv (recommended) or pip

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/knowledge-agent
cd knowledge-agent
```

2. Create virtual environment:
```bash
uv venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
playwright install
```

4. Copy environment file:
```bash
cp .env.example .env
```

5. Run tests to verify setup:
```bash
pytest tests/
```

## Project Structure

```
knowledge-agent/
├── app/                  # Application code
│   ├── main.py          # Entry point (Gradio)
│   ├── config.py        # Configuration
│   ├── state.py         # Queue & settings (JSON)
│   ├── db/              # Database layer (SQLite/SQLModel)
│   │   ├── models.py    # Extraction, ScrapeMetric, Trace
│   │   └── session.py   # DB session management
│   ├── services/        # Business logic
│   │   ├── scraper_service.py
│   │   ├── notification_service.py
│   │   ├── scheduler_service.py
│   │   └── optimization_service.py
│   └── ui/              # Gradio UI
│       ├── components/  # Reusable components
│       └── pages/      # Page implementations
├── scraper/             # Scraping engines
│   ├── engines/         # Individual scrapers
│   │   ├── simple_http_engine.py
│   │   ├── playwright_engine.py
│   │   ├── playwright_alt_engine.py
│   │   ├── playwright_tls_engine.py
│   │   └── cloudscraper_engine.py
│   ├── router.py        # URL routing
│   ├── runner.py        # Execution
│   ├── bm25_ranker.py   # Duplicate detection
│   └── method_optimizer.py
├── storage/             # File storage
│   ├── folder_manager.py
│   └── markdown_saver.py
├── utils/               # Utilities
│   ├── validators.py
│   ├── content_hasher.py
│   └── robots_checker.py
├── tests/               # Test suite
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
└── docs/               # Documentation
```

## Coding Standards

### Type Hints

All functions must include type hints:
```python
def process_url(url: str, options: dict[str, Any] | None = None) -> bool:
    ...
```

### Docstrings

Use Google-style docstrings:
```python
def function_name(param: str) -> bool:
    """Short description.

    Longer description if needed.

    Args:
        param: Description of parameter.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param is invalid.
    """
```

### Naming Conventions

- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

### Error Handling

- Never use bare `except:` - catch specific exceptions
- Always log errors with context
- Return meaningful error messages

### Database (SQLModel)

Use SQLModel for all database models:
```python
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class Extraction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(unique=True, index=True)
    file_path: str
    word_count: int
    scraper: str
    extracted_at: datetime = Field(default_factory=datetime.now)
```

## Testing

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Specific file
pytest tests/unit/test_validators.py

# With coverage
pytest --cov=app --cov=scraper
```

### Writing Tests

```python
# tests/unit/test_validators.py
import pytest
from utils.validators import is_valid_url

class TestValidators:
    def test_valid_url(self):
        assert is_valid_url("https://example.com") is True

    def test_invalid_url(self):
        assert is_valid_url("not-a-url") is False
```

### Test Fixtures

Use fixtures for common setup:
```python
@pytest.fixture
def sample_html():
    return "<html><body>Test content</body></html>"
```

## Submitting Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation

### Commit Messages

Use conventional commits:
```
feat: add BM25 duplicate detection
fix: resolve queue persistence issue
docs: update API documentation
refactor: simplify router logic
```

### Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure all tests pass
5. Update documentation if needed
6. Submit pull request

## Code Review

### Checklist

- [ ] Type hints on all functions
- [ ] Docstrings on public functions
- [ ] Tests for new functionality
- [ ] No bare except clauses
- [ ] Proper error handling
- [ ] Logging where appropriate

### Review Criteria

- Code correctness
- Test coverage
- Documentation
- Performance considerations
- Security implications

## Getting Help

- Open an issue for bugs
- Use discussions for questions
- Check existing issues before creating new ones

---

*This project follows the Python Foundation Style Guide and uses pytest for testing.*
