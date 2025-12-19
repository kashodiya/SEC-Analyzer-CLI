# Testing Guide - SEC Analyzer

## Overview

This guide covers how to test the SEC Analyzer, from basic functionality to full AI-powered risk analysis.

## Prerequisites

1. **Basic Setup**:
   ```bash
   cd sec-analyzer
   uv sync
   ```

2. **AWS Credentials** (for full analysis):
   ```bash
   # Option 1: Environment variables
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_DEFAULT_REGION=us-east-1

   # Option 2: AWS CLI
   aws configure
   ```

## Testing Levels

### Level 1: Basic CLI Testing (No AWS Required)

Test the CLI interface and SEC data fetching:

```bash
# Test CLI help
uv run sec-analyzer --help

# Test configuration display
uv run sec-analyzer config

# Test SEC data fetching (works without AWS)
uv run sec-analyzer filings AAPL --limit 5
uv run sec-analyzer filings JPM --limit 3
uv run sec-analyzer filings MSFT --limit 5
```

### Level 2: Cache Testing

Test the caching system:

```bash
# Check initial cache state
uv run sec-analyzer cache stats

# Warm cache with test data
uv run sec-analyzer cache warm AAPL JPM MSFT --report-type 10-K

# Check cache after warming
uv run sec-analyzer cache stats
uv run sec-analyzer cache performance

# Test cache hits by repeating requests
uv run sec-analyzer filings AAPL --limit 3
uv run sec-analyzer filings AAPL --limit 3  # Should be faster (cached)

# Check performance improvement
uv run sec-analyzer cache performance
```

### Level 3: Mock Analysis Testing

Create a mock version for testing without AWS:

```bash
# Create test script
cat > test_mock_analysis.py << 'EOF'
#!/usr/bin/env python3
"""Mock analysis test - simulates AI analysis without AWS Bedrock."""

import asyncio
import json
from datetime import datetime
from frb_sec_analyzer.config import Config
from frb_sec_analyzer.sec_client import SECClient

async def mock_analysis_test():
    """Test analysis workflow with mock AI responses."""
    
    print("🧪 Starting Mock Analysis Test")
    print("=" * 50)
    
    # Initialize components
    config = Config()
    sec_client = SECClient(config)
    await sec_client.initialize()
    
    # Test data fetching
    print("\n1. Testing SEC Data Fetching...")
    try:
        reports = await sec_client.get_company_reports("AAPL", "10-K")
        print(f"✅ Successfully fetched {len(reports)} reports for AAPL")
        
        if reports:
            report = reports[0]
            print(f"   - Form Type: {report.get('form_type')}")
            print(f"   - Filing Date: {report.get('filing_date')}")
            print(f"   - Content Length: {len(report.get('content', ''))} characters")
    except Exception as e:
        print(f"❌ Error fetching reports: {e}")
        return
    
    # Mock AI analysis
    print("\n2. Simulating AI Risk Analysis...")
    mock_analysis = {
        "ticker": "AAPL",
        "overall_risk_score": 6.5,
        "overall_risk_level": "Medium",
        "analysis_timestamp": datetime.now().isoformat(),
        "key_insights": [
            "Strong financial position with substantial cash reserves",
            "Market concentration risk in iPhone product line",
            "Supply chain dependencies in Asia present operational risks",
            "Regulatory scrutiny in multiple jurisdictions",
            "Climate transition risks from manufacturing operations"
        ],
        "risk_categories": {
            "credit_risk": {
                "level": "Low",
                "score": 3.0,
                "summary": "Excellent credit profile with minimal default risk"
            },
            "market_risk": {
                "level": "Medium", 
                "score": 6.0,
                "summary": "Exposure to consumer demand cycles and currency fluctuations"
            },
            "operational_risk": {
                "level": "Medium",
                "score": 7.0,
                "summary": "Supply chain concentration and cybersecurity concerns"
            },
            "liquidity_risk": {
                "level": "Low",
                "score": 2.0,
                "summary": "Strong liquidity position with significant cash holdings"
            }
        }
    }
    
    print("✅ Mock analysis completed")
    print(f"   - Overall Risk Level: {mock_analysis['overall_risk_level']}")
    print(f"   - Risk Score: {mock_analysis['overall_risk_score']}/10")
    print(f"   - Key Insights: {len(mock_analysis['key_insights'])} identified")
    
    # Test report generation
    print("\n3. Testing Report Generation...")
    from frb_sec_analyzer.report_generator import ReportGenerator
    
    report_gen = ReportGenerator(config)
    report = report_gen.generate_report(mock_analysis, "AAPL", "10-K")
    
    # Save test report
    with open("test_analysis_report.md", "w") as f:
        f.write(report)
    
    print("✅ Report generated successfully")
    print("   - Saved to: test_analysis_report.md")
    print(f"   - Report length: {len(report)} characters")
    
    print("\n🎉 Mock Analysis Test Completed Successfully!")
    print("\nNext Steps:")
    print("- Review test_analysis_report.md")
    print("- Configure AWS credentials for full AI analysis")
    print("- Run: uv run sec-analyzer analyze AAPL --report-type 10-K")

if __name__ == "__main__":
    asyncio.run(mock_analysis_test())
EOF

# Run mock test
uv run python test_mock_analysis.py
```

### Level 4: Full AI Analysis Testing (Requires AWS)

Test the complete AI-powered analysis:

```bash
# Test with a simple company first
uv run sec-analyzer analyze AAPL --report-type 10-K --verbose

# Test with output file
uv run sec-analyzer analyze JPM --report-type 10-K --output jpmorgan_analysis.md

# Test different report types
uv run sec-analyzer analyze MSFT --report-type 10-Q --verbose
```

## Test Scenarios

### Scenario 1: New User Workflow

```bash
# 1. Check configuration
uv run sec-analyzer config

# 2. Test basic functionality
uv run sec-analyzer filings AAPL --limit 3

# 3. Warm cache for better performance
uv run sec-analyzer cache warm AAPL --report-type 10-K

# 4. Run analysis (requires AWS)
uv run sec-analyzer analyze AAPL --report-type 10-K --output apple_analysis.md
```

### Scenario 2: Batch Analysis Testing

```bash
# Create batch test script
cat > batch_test.py << 'EOF'
#!/usr/bin/env python3
"""Batch analysis testing script."""

import subprocess
import time

companies = ["AAPL", "MSFT", "GOOGL"]
report_type = "10-K"

print("🚀 Starting Batch Analysis Test")

for company in companies:
    print(f"\n📊 Analyzing {company}...")
    
    try:
        # Run analysis
        result = subprocess.run([
            "uv", "run", "sec-analyzer", "analyze", 
            company, "--report-type", report_type,
            "--output", f"{company.lower()}_analysis.md"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {company} analysis completed")
        else:
            print(f"❌ {company} analysis failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {company} analysis timed out")
    except Exception as e:
        print(f"❌ {company} analysis error: {e}")
    
    # Brief pause between analyses
    time.sleep(5)

print("\n🎉 Batch Analysis Test Completed")
EOF

# Run batch test (requires AWS)
python batch_test.py
```

### Scenario 3: Performance Testing

```bash
# Create performance test
cat > performance_test.py << 'EOF'
#!/usr/bin/env python3
"""Performance testing script."""

import subprocess
import time
import json

def run_command_timed(cmd):
    """Run command and measure execution time."""
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    return result, end_time - start_time

def test_performance():
    """Test various operations and measure performance."""
    
    print("⚡ Performance Testing")
    print("=" * 40)
    
    tests = [
        (["uv", "run", "sec-analyzer", "config"], "Configuration Display"),
        (["uv", "run", "sec-analyzer", "cache", "stats"], "Cache Statistics"),
        (["uv", "run", "sec-analyzer", "filings", "AAPL", "--limit", "5"], "SEC Filings (First Time)"),
        (["uv", "run", "sec-analyzer", "filings", "AAPL", "--limit", "5"], "SEC Filings (Cached)"),
        (["uv", "run", "sec-analyzer", "cache", "performance"], "Cache Performance"),
    ]
    
    results = []
    
    for cmd, description in tests:
        print(f"\n🧪 Testing: {description}")
        result, duration = run_command_timed(cmd)
        
        if result.returncode == 0:
            print(f"✅ Success - {duration:.2f}s")
            results.append({"test": description, "duration": duration, "status": "success"})
        else:
            print(f"❌ Failed - {duration:.2f}s")
            results.append({"test": description, "duration": duration, "status": "failed"})
    
    # Save results
    with open("performance_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Performance Results Summary:")
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {result['test']}: {result['duration']:.2f}s")

if __name__ == "__main__":
    test_performance()
EOF

# Run performance test
python performance_test.py
```

## Troubleshooting Common Issues

### Issue 1: AWS Credentials Not Found

```bash
# Check AWS configuration
aws sts get-caller-identity

# If not configured, set up credentials
aws configure
# OR
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### Issue 2: SEC API Rate Limiting

```bash
# The tool has built-in rate limiting, but if you see errors:
# - Wait a few minutes between requests
# - Use cache warming during off-hours
# - Check cache stats to ensure caching is working

uv run sec-analyzer cache stats
```

### Issue 3: Model Access Issues

```bash
# Verify model access in AWS Bedrock console
# Ensure you have permissions for:
# - us.anthropic.claude-sonnet-4-20250514-v1:0
# - us.anthropic.claude-opus-4-1-20250805-v1:0

# Test with a simple AWS CLI call
aws bedrock list-foundation-models --region us-east-1
```

## Expected Test Results

### Successful Basic Test Output:
```
Recent SEC Filings for AAPL
┌────────────┬───────────┬──────────────────┬────────────────────────────────┐
│ Date       │ Form Type │ Description      │ URL                            │
├────────────┼───────────┼──────────────────┼────────────────────────────────┤
│ 2025-12-05 │ 8-K       │ 8-K Filing...    │ https://data.sec.gov/Archives… │
│ 2025-11-14 │ 4         │ 4 Filing...      │ https://data.sec.gov/Archives… │
│ 2025-11-14 │ 25-NSE    │ 25-NSE Filing... │ https://data.sec.gov/Archives… │
└────────────┴───────────┴──────────────────┴────────────────────────────────┘
```

### Successful Analysis Output:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRB SEC Risk Analysis                             │
│ Company: AAPL                                                               │
│ Report Type: 10-K                                                           │
└─────────────────────────────────────────────────────────────────────────────┘

Risk Assessment Summary - AAPL
┌──────────────────┬────────┬───────┬─────────────────────────────────────────┐
│ Risk Category    │ Level  │ Score │ Key Concerns                            │
├──────────────────┼────────┼───────┼─────────────────────────────────────────┤
│ Credit Risk      │ Low    │ 3     │ Strong financial position...            │
│ Market Risk      │ Medium │ 6     │ Consumer demand cycles...               │
│ Operational Risk │ Medium │ 7     │ Supply chain concentration...           │
└──────────────────┴────────┴───────┴─────────────────────────────────────────┘

Overall Risk Score: 6.5
Risk Level: Medium
```

## Automated Testing Script

Create a comprehensive test runner:

```bash
# Create comprehensive test runner
cat > run_all_tests.py << 'EOF'
#!/usr/bin/env python3
"""Comprehensive test runner for FRB SEC Analyzer."""

import subprocess
import sys
import time
from datetime import datetime

def run_test_suite():
    """Run complete test suite."""
    
    print("🧪 FRB SEC Analyzer - Comprehensive Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    
    tests = [
        ("Basic CLI", ["uv", "run", "frb-sec-analyzer", "--help"]),
        ("Configuration", ["uv", "run", "frb-sec-analyzer", "config"]),
        ("Cache Stats", ["uv", "run", "frb-sec-analyzer", "cache", "stats"]),
        ("SEC Filings", ["uv", "run", "frb-sec-analyzer", "filings", "AAPL", "--limit", "3"]),
        ("Cache Performance", ["uv", "run", "frb-sec-analyzer", "cache", "performance"]),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, cmd in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f"✅ PASSED: {test_name}")
                passed += 1
            else:
                print(f"❌ FAILED: {test_name}")
                print(f"   Error: {result.stderr[:200]}")
                failed += 1
        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT: {test_name}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test_name} - {e}")
            failed += 1
    
    print(f"\n📊 Test Results Summary:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Ready for analysis.")
        print("\nNext step: Run analysis with AWS credentials:")
        print("uv run sec-analyzer analyze AAPL --report-type 10-K")
    else:
        print(f"\n⚠️  {failed} tests failed. Check configuration and dependencies.")

if __name__ == "__main__":
    run_test_suite()
EOF

# Run all tests
python run_all_tests.py
```

This comprehensive testing guide covers everything from basic functionality to full AI analysis, helping you verify that the SEC Analyzer is working correctly at each level.