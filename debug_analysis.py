#!/usr/bin/env python3
"""Debug script to test AAPL analysis step by step."""

import asyncio
import json
from src.sec_analyzer.config import Config
from src.sec_analyzer.sec_client import SECClient
from src.sec_analyzer.risk_analyzer import RiskAnalyzer

async def debug_analysis():
    """Debug the analysis process step by step."""
    
    print("=== SEC Analyzer Debug ===")
    
    # Initialize config
    config = Config()
    print(f"✓ Config loaded - AWS Region: {config.aws_region}")
    
    # Initialize SEC client
    print("\n=== Testing SEC Client ===")
    sec_client = SECClient(config)
    await sec_client.initialize()
    print("✓ SEC Client initialized")
    
    # Test fetching reports
    try:
        reports = await sec_client.get_company_reports("AAPL", "10-K")
        print(f"✓ Found {len(reports)} reports for AAPL")
        
        for i, report in enumerate(reports):
            print(f"\nReport {i+1}:")
            print(f"  Form: {report.get('form_type', 'N/A')}")
            print(f"  Date: {report.get('filing_date', 'N/A')}")
            print(f"  Content length: {len(report.get('content', ''))}")
            print(f"  Content preview: {report.get('content', '')[:200]}...")
            
    except Exception as e:
        print(f"✗ Error fetching reports: {e}")
        return
    
    # Test risk analyzer
    print("\n=== Testing Risk Analyzer ===")
    risk_analyzer = RiskAnalyzer(config)
    await risk_analyzer.initialize()
    print("✓ Risk Analyzer initialized")
    
    try:
        # Test with a small sample
        sample_reports = reports[:1]  # Just use first report
        print(f"Analyzing {len(sample_reports)} reports...")
        
        analysis_results = await risk_analyzer.analyze_reports(sample_reports, "AAPL", "10-K")
        print("✓ Analysis completed")
        
        print("\n=== Analysis Results ===")
        print(json.dumps(analysis_results, indent=2, default=str))
        
    except Exception as e:
        print(f"✗ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_analysis())