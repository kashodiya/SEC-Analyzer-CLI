# SEC Analyzer

A CLI tool for analysts to assess company risks and insights from SEC reports using AI agents powered by AWS Bedrock and Strands Agents framework.

## Features

- **AI-Powered Risk Analysis**: Uses specialized AI agents to analyze different risk categories
- **SEC EDGAR Integration**: Automatically fetches and processes SEC filings (10-K, 10-Q, 8-K) using edgartools
- **Multi-Agent Analysis**: Employs specialized agents for financial, operational, and strategic risk assessment
- **Comprehensive Reporting**: Generates detailed risk assessment reports
- **AWS Bedrock Integration**: Leverages Claude models for advanced natural language understanding
- **Advanced Caching System**: SQLite-based caching with compression, performance tracking, and automatic management
- **Cache Warming**: Pre-load data for faster analysis during business hours
- **Performance Analytics**: Track cache hit rates and response times for optimization

## Installation

### Prerequisites

- Python 3.11+
- UV package manager
- AWS credentials configured for Bedrock access
- Access to us-east-1 region with Bedrock models

### Setup

1. Clone and navigate to the project:
```bash
cd sec-analyzer
```

2. Install dependencies using UV:
```bash
uv sync
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Install the CLI tool:
```bash
uv pip install -e .
```

## Usage

### Basic Analysis

Analyze a company's 10-K filings:
```bash
sec-analyzer analyze AAPL
```

Analyze specific report types:
```bash
sec-analyzer analyze AAPL --report-type 10-Q
sec-analyzer analyze AAPL --report-type 8-K
sec-analyzer analyze AAPL --report-type all
```

Save analysis to file:
```bash
sec-analyzer analyze AAPL --output aapl_analysis.md
```

### List Recent Filings

View recent SEC filings for a company:
```bash
sec-analyzer filings AAPL --limit 10
```

### Cache Management

The tool includes an advanced caching system to avoid repeated downloads:

```bash
# Show cache statistics
sec-analyzer cache stats

# Show performance analytics
sec-analyzer cache performance

# Warm cache for faster analysis
sec-analyzer cache warm JPM BAC WFC --report-type 10-K

# Clean up expired entries
sec-analyzer cache cleanup

# Clear all cache data
sec-analyzer cache clear
```

### Configuration

View current configuration:
```bash
sec-analyzer config
```

## Risk Categories Analyzed

The tool analyzes the following risk categories:

1. **Credit Risk** - Loan losses, credit quality, concentration risk
2. **Market Risk** - Interest rate, FX, commodity exposures  
3. **Operational Risk** - Cybersecurity, operational failures, controls
4. **Liquidity Risk** - Funding sources, liquidity ratios
5. **Regulatory Risk** - Compliance issues, regulatory changes
6. **Cybersecurity Risk** - Technology vulnerabilities, data breaches
7. **Climate Risk** - Climate-related financial risks
8. **Reputation Risk** - ESG factors, reputation threats

## AI Agent Architecture

The tool uses a multi-agent approach with specialized roles:

- **Financial Risk Analyst**: Focuses on credit, market, and liquidity risks
- **Operational Risk Specialist**: Analyzes operational and cybersecurity risks  
- **Strategic Risk Analyst**: Assesses climate, reputation, and strategic risks
- **Chief Risk Officer**: Synthesizes findings into comprehensive assessment

## Configuration Options

Environment variables (prefix with `SEC_ANALYZER_`):

- `AWS_REGION`: AWS region (default: us-east-1)
- `BEDROCK_MODEL`: Bedrock model ID (default: claude-sonnet-4)
- `API_BASE_URL`: SEC API base URL
- `USER_AGENT`: User agent for SEC API requests
- `MAX_REPORT_LENGTH`: Maximum characters to analyze per report
- `AGENT_TEMPERATURE`: AI model temperature (0.0-1.0)
- `AGENT_MAX_TOKENS`: Maximum tokens per AI response
- `CACHE_ENABLED`: Enable/disable caching (default: true)
- `CACHE_DB_PATH`: SQLite database path (default: sec_analyzer_cache.db)
- `CACHE_EXPIRY_DAYS`: Cache expiration in days (default: 7)
- `CACHE_COMPRESSION`: Enable data compression (default: true)
- `CACHE_MAX_SIZE_MB`: Maximum cache size in MB (default: 500)

## AWS Bedrock Models

Supported models in us-east-1:
- `us.anthropic.claude-sonnet-4-20250514-v1:0` (default)
- `us.anthropic.claude-opus-4-1-20250805-v1:0`

## Output Format

The tool generates:
- **Console Output**: Rich formatted tables and summaries
- **Markdown Reports**: Comprehensive analysis reports
- **JSON Data**: Structured data for programmatic use

## Rate Limiting

The tool uses edgartools for SEC data access, which automatically handles SEC EDGAR API rate limits (10 requests per second) and includes appropriate delays between requests.

## Security & Compliance

- Uses edgartools library for compliant SEC EDGAR data access
- Includes proper User-Agent identification
- Respects rate limiting requirements
- Designed for internal use with appropriate disclaimers

## Development

### Project Structure

```
sec-analyzer/
├── src/sec_analyzer/
│   ├── __init__.py
│   ├── cli.py              # Main CLI interface
│   ├── config.py           # Configuration management
│   ├── sec_client.py       # SEC data client using edgartools
│   ├── risk_analyzer.py    # AI risk analysis agents
│   └── report_generator.py # Report generation
├── pyproject.toml          # Project configuration
├── .env.example           # Environment template
└── README.md
```

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
uv run ruff check
uv run black .
```

## License

Internal tool - not for external distribution.

## Support

For issues or questions, contact the development team.