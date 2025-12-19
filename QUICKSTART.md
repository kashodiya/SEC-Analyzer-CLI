# Quick Start Guide

## Installation

1. Ensure UV is installed:
```bash
uv --version
```

2. Install the CLI tool:
```bash
cd frb-sec-analyzer
uv sync
```

## Basic Usage

### 1. Check Configuration

View your current configuration:
```bash
uv run frb-sec-analyzer config
```

### 2. List Recent Filings

See what SEC filings are available for a company:
```bash
uv run frb-sec-analyzer filings AAPL --limit 10
uv run frb-sec-analyzer filings JPM --limit 5
```

### 3. Analyze Company Risks

Analyze 10-K filings (annual reports):
```bash
uv run frb-sec-analyzer analyze AAPL
```

Analyze 10-Q filings (quarterly reports):
```bash
uv run frb-sec-analyzer analyze AAPL --report-type 10-Q
```

Analyze all available filings:
```bash
uv run frb-sec-analyzer analyze AAPL --report-type all
```

Save analysis to a file:
```bash
uv run frb-sec-analyzer analyze AAPL --output aapl_risk_analysis.md
```

Enable verbose output:
```bash
uv run frb-sec-analyzer analyze AAPL --verbose
```

## Example Workflow

```bash
# 1. Check what filings are available
uv run frb-sec-analyzer filings JPM --limit 5

# 2. Analyze the most recent 10-K
uv run frb-sec-analyzer analyze JPM --report-type 10-K

# 3. Save detailed analysis to file
uv run frb-sec-analyzer analyze JPM --report-type 10-K --output jpmorgan_analysis.md --verbose
```

## Common Company Tickers

Financial Institutions:
- JPM - JPMorgan Chase
- BAC - Bank of America
- WFC - Wells Fargo
- C - Citigroup
- GS - Goldman Sachs
- MS - Morgan Stanley

Tech Companies:
- AAPL - Apple
- MSFT - Microsoft
- GOOGL - Alphabet (Google)
- AMZN - Amazon

## Environment Configuration

Create a `.env` file to customize settings:

```bash
cp .env.example .env
```

Edit `.env` to configure:
- AWS region
- Bedrock model selection
- SEC API settings
- Analysis parameters

## AWS Credentials

Ensure your AWS credentials are configured for Bedrock access:

```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Option 2: AWS CLI configuration
aws configure
```

## Troubleshooting

### "No module named 'strands'"
Run `uv sync` to install dependencies.

### "Could not find CIK for ticker"
Verify the ticker symbol is correct and the company files with the SEC.

### "Rate limit exceeded"
The tool respects SEC rate limits. Wait a moment and try again.

### AWS Bedrock Access Denied
Ensure your AWS credentials have permissions for:
- bedrock-runtime:InvokeModel
- Access to the specified model in us-east-1

## Next Steps

- Review the full README.md for detailed documentation
- Customize risk categories in config.py
- Adjust analysis parameters in .env file
- Integrate with your existing risk management workflows