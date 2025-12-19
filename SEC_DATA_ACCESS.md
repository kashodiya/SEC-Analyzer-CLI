# SEC Data Access Guidelines

## Important: Use edgartools Only

This project **MUST** use [edgartools](https://github.com/dgunning/edgartools) for all SEC data retrieval. Do not make direct API calls to the SEC website.

## Why edgartools?

1. **Compliance**: edgartools handles SEC rate limiting and user agent requirements automatically
2. **Reliability**: Built-in error handling and retry logic
3. **Ease of use**: Simplified API for common SEC data operations
4. **Maintenance**: Actively maintained and updated for SEC API changes

## Current Implementation

The main SEC client (`src/frb_sec_analyzer/sec_client.py`) properly uses edgartools:

```python
from edgar import Company, Filing, get_filings, set_identity

# Get company data
company = Company(ticker)
filings = company.get_filings(form='10-K', limit=5)
```

## Test Files

Some test and debug files (`test_sec_alternative.py`, `debug_*.py`) make direct SEC API calls for testing purposes only. These should NOT be used as examples for production code.

## Dependencies

edgartools is included in `pyproject.toml`:

```toml
dependencies = [
    "edgartools>=2.0.0",
    # ... other dependencies
]
```

## Configuration

The user agent is configured in `config.py` and passed to edgartools via `set_identity()`:

```python
set_identity(config.user_agent)
```

## Do NOT Use

- Direct HTTP requests to `data.sec.gov`
- Direct HTTP requests to `edgar.sec.gov`
- Manual URL construction for SEC endpoints
- Raw `requests` or `httpx` calls to SEC APIs

## Always Use

- `edgar.Company(ticker)` for company data
- `company.get_filings()` for filing data
- `filing.text()` or `filing.html()` for document content
- edgartools built-in methods for all SEC operations