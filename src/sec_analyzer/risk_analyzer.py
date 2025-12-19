"""AI-powered risk analysis using AWS Bedrock directly."""

import json
import boto3
import hashlib
from datetime import datetime
from typing import List, Dict, Any

from .config import Config
from .cache_manager import CacheManager


class RiskAnalyzer:
    """AI agent for analyzing SEC reports and assessing risks."""
    
    def __init__(self, config: Config):
        self.config = config
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=config.aws_region
        )
        
        # Initialize cache
        self.cache = CacheManager(config)
    
    async def initialize(self):
        """Initialize the risk analyzer and cache."""
        await self.cache.initialize()
    
    async def _call_bedrock(self, prompt: str) -> str:
        """Make a direct call to AWS Bedrock."""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.config.agent_max_tokens,
            "temperature": self.config.agent_temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = self.bedrock_client.invoke_model(
            modelId=self.config.bedrock_model,
            body=json.dumps(request_body),
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        
        if 'content' in response_body and response_body['content']:
            return response_body['content'][0]['text']
        else:
            return "No response generated"
    
    async def analyze_reports(self, reports: List[Dict], ticker: str, report_type: str = "10-K") -> Dict[str, Any]:
        """Analyze SEC reports using direct Bedrock calls to assess various risk categories."""
        
        # Prepare report content for analysis
        report_content = self._prepare_report_content(reports)
        
        # Generate content hash for caching
        content_hash = hashlib.md5(report_content.encode()).hexdigest()
        
        # Try to get cached analysis results
        cached_analysis = await self.cache.get_analysis_results(ticker, report_type, content_hash)
        if cached_analysis:
            return cached_analysis
        
        # Analyze with financial risk assessment
        financial_prompt = f"""You are a financial risk analyst. Analyze the SEC filings for {ticker} and assess financial risks:
        
        Report Content:
        {report_content}
        
        Focus on:
        1. Credit risk indicators (loan losses, credit quality, concentration risk)
        2. Market risk exposures (interest rate, foreign exchange, commodity risks)  
        3. Liquidity risk factors (funding sources, liquidity ratios, stress scenarios)
        4. Capital adequacy and leverage metrics
        
        Provide a risk score (1-10) and detailed assessment for each category.
        Format your response as JSON with the following structure:
        {{
            "financial_risks": {{
                "credit_risk": {{"score": X, "assessment": "detailed analysis"}},
                "market_risk": {{"score": X, "assessment": "detailed analysis"}},
                "liquidity_risk": {{"score": X, "assessment": "detailed analysis"}},
                "capital_risk": {{"score": X, "assessment": "detailed analysis"}}
            }},
            "overall_financial_score": X,
            "key_concerns": ["concern1", "concern2", "concern3"]
        }}"""
        
        financial_analysis = await self._call_bedrock(financial_prompt)
        
        # Analyze with operational risk assessment
        operational_prompt = f"""You are an operational risk analyst. Analyze the SEC filings for {ticker} and assess operational risks:
        
        Report Content:
        {report_content}
        
        Focus on:
        1. Cybersecurity incidents and vulnerabilities
        2. Operational failures and control weaknesses
        3. Regulatory compliance issues and violations
        4. Technology and system risks
        5. Human capital and key person risks
        
        Provide a risk score (1-10) and detailed assessment for each category.
        Format your response as JSON with the following structure:
        {{
            "operational_risks": {{
                "cybersecurity_risk": {{"score": X, "assessment": "detailed analysis"}},
                "operational_failures": {{"score": X, "assessment": "detailed analysis"}},
                "compliance_risk": {{"score": X, "assessment": "detailed analysis"}},
                "technology_risk": {{"score": X, "assessment": "detailed analysis"}},
                "human_capital_risk": {{"score": X, "assessment": "detailed analysis"}}
            }},
            "overall_operational_score": X,
            "key_concerns": ["concern1", "concern2", "concern3"]
        }}"""
        
        operational_analysis = await self._call_bedrock(operational_prompt)
        
        # Analyze with strategic risk assessment
        strategic_prompt = f"""You are a strategic risk analyst. Analyze the SEC filings for {ticker} and assess strategic risks:
        
        Report Content:
        {report_content}
        
        Focus on:
        1. Climate-related financial risks and transition risks
        2. Business model sustainability and competitive threats
        3. Reputation risks and ESG factors
        4. Regulatory and policy change impacts
        5. Strategic execution risks
        
        Provide a risk score (1-10) and detailed assessment for each category.
        Format your response as JSON with the following structure:
        {{
            "strategic_risks": {{
                "climate_risk": {{"score": X, "assessment": "detailed analysis"}},
                "business_model_risk": {{"score": X, "assessment": "detailed analysis"}},
                "reputation_risk": {{"score": X, "assessment": "detailed analysis"}},
                "regulatory_risk": {{"score": X, "assessment": "detailed analysis"}},
                "execution_risk": {{"score": X, "assessment": "detailed analysis"}}
            }},
            "overall_strategic_score": X,
            "key_concerns": ["concern1", "concern2", "concern3"]
        }}"""
        
        strategic_analysis = await self._call_bedrock(strategic_prompt)
        
        # Synthesize results
        synthesis_prompt = f"""You are a senior risk analyst. Synthesize the risk assessments from financial, operational, and strategic 
        analysts for {ticker} into a comprehensive risk profile:
        
        Financial Risk Analysis: {financial_analysis}
        Operational Risk Analysis: {operational_analysis}  
        Strategic Risk Analysis: {strategic_analysis}
        
        Provide:
        1. Overall risk score (1-10) and risk level (Low/Medium/High/Critical)
        2. Top 5 key risk concerns
        3. Risk trend analysis (Improving/Stable/Deteriorating)
        4. Regulatory implications for oversight
        5. Recommended monitoring priorities
        
        Format your response as JSON with the following structure:
        {{
            "overall_risk_score": X,
            "overall_risk_level": "Low/Medium/High/Critical",
            "top_risk_concerns": ["concern1", "concern2", "concern3", "concern4", "concern5"],
            "risk_trend": "Improving/Stable/Deteriorating",
            "regulatory_implications": "detailed analysis for regulatory oversight",
            "monitoring_priorities": ["priority1", "priority2", "priority3"],
            "financial_analysis": {financial_analysis},
            "operational_analysis": {operational_analysis},
            "strategic_analysis": {strategic_analysis}
        }}"""
        
        synthesis_result = await self._call_bedrock(synthesis_prompt)
        
        # Parse and structure results
        analysis_results = self._parse_analysis_results(synthesis_result, ticker)
        
        # Cache the analysis results
        await self.cache.cache_analysis_results(ticker, report_type, content_hash, analysis_results)
        
        return analysis_results
    
    def _prepare_report_content(self, reports: List[Dict]) -> str:
        """Prepare and clean report content for analysis."""
        content_parts = []
        
        for report in reports:
            if 'content' in report and report['content']:
                content_parts.append(f"""
=== {report['form_type']} Filing - {report['filing_date']} ===
{report['content'][:15000]}  # Limit content per report
""")
        
        return "\n".join(content_parts)
    
    def _parse_analysis_results(self, result: str, ticker: str) -> Dict[str, Any]:
        """Parse and structure the analysis results from Bedrock."""
        
        try:
            # Try to extract JSON from the response
            structured_result = self._extract_structured_data(result)
            
            # Ensure we have required fields
            if not structured_result:
                structured_result = {
                    'overall_risk_score': 'N/A',
                    'overall_risk_level': 'Unknown',
                    'top_risk_concerns': ['Analysis completed but results could not be parsed'],
                    'risk_categories': {}
                }
            
            # Add metadata
            structured_result['ticker'] = ticker
            structured_result['analysis_timestamp'] = str(datetime.now())
            structured_result['raw_analysis'] = result
            
            return structured_result
            
        except Exception as e:
            return {
                'ticker': ticker,
                'error': f"Error parsing analysis results: {e}",
                'overall_risk_score': 'N/A',
                'overall_risk_level': 'Unknown',
                'top_risk_concerns': ['Analysis failed - please check logs'],
                'risk_categories': {},
                'raw_analysis': result
            }
    
    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from AI agent response."""
        
        # Try to find JSON in the response
        import re
        
        json_pattern = r'\{.*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # If no JSON found, create structured response from text
        return self._create_structured_from_text(text)
    
    def _create_structured_from_text(self, text: str) -> Dict[str, Any]:
        """Create structured response from unstructured text."""
        
        # Extract key insights using simple text processing
        lines = text.split('\n')
        concerns = []
        risk_categories = {}
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 20:
                if any(keyword in line.lower() for keyword in ['risk', 'concern', 'issue', 'threat']):
                    concerns.append(line[:200])  # Limit length
                    
                if len(concerns) >= 10:  # Limit number of concerns
                    break
        
        # Try to extract overall assessment
        overall_score = 'N/A'
        overall_level = 'Medium'  # Default
        
        if 'high risk' in text.lower() or 'critical' in text.lower():
            overall_level = 'High'
        elif 'low risk' in text.lower():
            overall_level = 'Low'
        
        return {
            'overall_risk_score': overall_score,
            'overall_risk_level': overall_level,
            'top_risk_concerns': concerns[:5],  # Top 5 concerns
            'risk_categories': risk_categories,
            'monitoring_priorities': ['Review financial statements', 'Monitor regulatory compliance'],
            'risk_trend': 'Stable'
        }