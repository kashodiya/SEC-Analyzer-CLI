# Real Analysis Testing Guide

## Overview

This guide shows you how to test the SEC Analyzer with real SEC data and AI-powered risk analysis using AWS Bedrock.

## Prerequisites

### 1. AWS Credentials Setup

Since the system needs AWS Bedrock access, you need to configure credentials:

#### Option A: EC2 Instance Role (Recommended for Production)
If running on EC2 with an IAM role:
```bash
# Verify role access
aws sts get-caller-identity

# If this works, you have role-based access
# Set the region explicitly
export AWS_DEFAULT_REGION=us-east-1
```

#### Option B: AWS Credentials (For Testing)
```bash
# Configure AWS CLI
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Enter region: us-east-1
# Enter output format: json

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### 2. Required AWS Permissions

Your IAM role/user needs these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-1::foundation-model/us.anthropic.claude-sonnet-4-20250514-v1:0",
                "arn:aws:bedrock:us-east-1::foundation-model/us.anthropic.claude-opus-4-1-20250805-v1:0"
            ]
        }
    ]
}
```

## Testing Steps

### Step 1: Verify Basic Functionality

```bash
# Test CLI and SEC data access (no AWS required)
uv run sec-analyzer --help
uv run sec-analyzer config
uv run sec-analyzer filings AAPL --limit 5
```

### Step 2: Test AWS Bedrock Access

```bash
# Test direct Bedrock access
export AWS_DEFAULT_REGION=us-east-1
uv run python test_bedrock_direct.py
```

Expected output if working:
```
✅ Bedrock Access Test SUCCESSFUL!
• AWS Bedrock client initialized correctly
• Claude model is accessible  
• AI response generated successfully
```

### Step 3: Run Real Analysis

Once Bedrock access is confirmed:

```bash
# Simple analysis
export AWS_DEFAULT_REGION=us-east-1
uv run sec-analyzer analyze AAPL --report-type 10-K

# Analysis with output file
uv run sec-analyzer analyze AAPL --report-type 10-K --output apple_analysis.md

# Verbose analysis
uv run sec-analyzer analyze AAPL --report-type 10-K --verbose
```

### Step 4: Test Different Companies and Report Types

```bash
# Financial institutions
uv run sec-analyzer analyze JPM --report-type 10-K --output jpmorgan_analysis.md
uv run sec-analyzer analyze BAC --report-type 10-Q --output bofa_analysis.md

# Technology companies  
uv run sec-analyzer analyze MSFT --report-type 10-K --output microsoft_analysis.md
uv run sec-analyzer analyze GOOGL --report-type 10-Q --output google_analysis.md
```

## Expected Real Analysis Output

### Console Output:
```
╭─────────────────────────────────────── Analysis Started ───────────────────────────────────────╮
│ FRB SEC Risk Analysis                                                                          │
│ Company: AAPL                                                                                  │
│ Report Type: 10-K                                                                              │
╰────────────────────────────────────────────────────────────────────────────────────────────────╯

✓ Initializing SEC client...
✓ Initializing AI risk analyzer...  
✓ Fetching 10-K reports for AAPL...
✓ Analyzing risks with AI agent...
✓ Generating analysis report...

Risk Assessment Summary - AAPL
┌──────────────────┬────────┬───────┬─────────────────────────────────────────┐
│ Risk Category    │ Level  │ Score │ Key Concerns                            │
├──────────────────┼────────┼───────┼─────────────────────────────────────────┤
│ Credit Risk      │ Low    │ 3.2   │ Strong balance sheet, minimal debt...  │
│ Market Risk      │ Medium │ 6.8   │ Consumer demand cycles, competition...  │
│ Operational Risk │ Medium │ 7.1   │ Supply chain dependencies, cyber...     │
│ Liquidity Risk   │ Low    │ 2.5   │ Substantial cash reserves...            │
│ Regulatory Risk  │ Medium │ 6.5   │ Antitrust scrutiny, privacy regs...     │
│ Climate Risk     │ Medium │ 5.8   │ Supply chain carbon footprint...        │
└──────────────────┴────────┴───────┴─────────────────────────────────────────┘

Key Insights:
• Strong financial position with $150B+ cash reserves
• iPhone revenue concentration presents market risk
• Supply chain dependencies in Asia create operational exposure
• Regulatory scrutiny increasing across multiple jurisdictions
• Climate commitments require significant operational changes

╭─────────────────────────────────────────── Summary ────────────────────────────────────────────╮
│ Overall Risk Score: 6.2                                                                        │
│ Risk Level: Medium                                                                             │
╰────────────────────────────────────────────────────────────────────────────────────────────────╯

Report saved to apple_analysis.md
```

### Generated Report Structure:
```markdown
# FRB SEC Risk Analysis Report

**Company:** AAPL
**Report Type:** 10-K
**Analysis Date:** 2025-12-19 12:00:00
**Generated by:** FRB SEC Analyzer v0.1.0

## Executive Summary
**Overall Risk Level:** Medium
**Overall Risk Score:** 6.2

The analysis indicates a Medium risk profile driven by market concentration 
in iPhone products and operational dependencies in Asian supply chains...

## Risk Assessment by Category

### Credit Risk
**Risk Level:** Low  
**Risk Score:** 3.2
Strong credit profile with minimal debt and substantial cash reserves...

### Market Risk  
**Risk Level:** Medium
**Risk Score:** 6.8
Exposure to consumer demand cycles and competitive pressures...

[Additional detailed analysis for each risk category]

## Key Risk Insights
1. Strong financial position with $150B+ cash reserves
2. iPhone revenue concentration presents market risk
3. Supply chain dependencies create operational exposure
4. Regulatory scrutiny increasing globally
5. Climate commitments require operational changes

## Regulatory Implications
Based on the Medium risk profile, this entity may warrant:
- Standard supervisory monitoring with attention to identified areas
- Review of risk management practices during examinations
- Monitoring of key risk indicator trends

## Monitoring Recommendations
1. Regular review of SEC filings for emerging risks
2. Monitor iPhone sales trends and diversification efforts  
3. Assess supply chain risk mitigation strategies
4. Track regulatory developments in key markets
5. Review climate risk management implementation
```

## Troubleshooting

### Issue: "Unable to locate credentials"
**Solution:**
```bash
# Check AWS configuration
aws sts get-caller-identity

# If fails, configure credentials
aws configure
# OR
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### Issue: "Access Denied" for Bedrock
**Solution:**
- Verify IAM permissions include `bedrock:InvokeModel`
- Check model is available in us-east-1 region
- Confirm model IDs are correct

### Issue: Analysis returns empty results
**Solution:**
- Check SEC data was fetched successfully
- Verify Bedrock model responses
- Review verbose output for errors

### Issue: Rate limiting errors
**Solution:**
- Use cache warming: `uv run sec-analyzer cache warm AAPL --report-type 10-K`
- Wait between analyses
- Check cache hit rates: `uv run sec-analyzer cache performance`

## Performance Optimization

### Cache Warming for Better Performance
```bash
# Warm cache for frequently analyzed companies
uv run sec-analyzer cache warm JPM BAC WFC C GS MS --report-type 10-K

# Check cache effectiveness
uv run sec-analyzer cache stats
uv run sec-analyzer cache performance
```

### Batch Analysis
```bash
# Create batch script
#!/bin/bash
companies=("JPM" "BAC" "WFC" "C" "GS" "MS")
for company in "${companies[@]}"; do
    echo "Analyzing $company..."
    uv run sec-analyzer analyze $company --report-type 10-K --output "${company}_analysis.md"
    sleep 10  # Rate limiting
done
```

## Production Deployment

### Environment Variables
```bash
# Set in production environment
export AWS_DEFAULT_REGION=us-east-1
export FRB_SEC_BEDROCK_MODEL=us.anthropic.claude-sonnet-4-20250514-v1:0
export FRB_SEC_CACHE_ENABLED=true
export FRB_SEC_CACHE_EXPIRY_DAYS=7
export FRB_SEC_USER_AGENT="FRB SEC Analyzer (your.email@frb.org)"
```

### Monitoring
```bash
# Regular cache maintenance
uv run sec-analyzer cache cleanup

# Performance monitoring
uv run sec-analyzer cache performance

# System health check
uv run python test_bedrock_direct.py
```

## Success Criteria

The real analysis is working correctly when you see:

1. ✅ **SEC Data Fetching**: Recent filings displayed correctly
2. ✅ **Cache Performance**: Hit rates > 30% after warming
3. ✅ **Bedrock Access**: Direct test passes without errors
4. ✅ **AI Analysis**: Risk categories populated with scores
5. ✅ **Report Generation**: Comprehensive markdown reports created
6. ✅ **Performance**: Analysis completes in 2-5 minutes

## Next Steps

Once real analysis is working:

1. **Integrate with workflows**: Set up scheduled analyses
2. **Customize risk categories**: Modify for specific FRB needs
3. **Dashboard integration**: Connect to visualization tools
4. **Automated reporting**: Schedule regular risk assessments
5. **Alert systems**: Set up notifications for high-risk findings

The FRB SEC Analyzer is now ready for production use with real SEC data and AI-powered risk analysis!