"""Configuration management for SEC Analyzer."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config(BaseModel):
    """Configuration settings for the SEC Analyzer."""
    
    # AWS Bedrock Configuration
    aws_region: str = Field(default="us-east-1")
    bedrock_model: str = Field(default="us.anthropic.claude-sonnet-4-20250514-v1:0")
    
    # Alternative model option
    bedrock_model_opus: str = Field(default="us.anthropic.claude-opus-4-1-20250805-v1:0")
    
    # SEC Data Configuration (via edgartools)
    # Note: All SEC data access should use edgartools, not direct API calls
    user_agent: str = Field(default="SEC Analyzer (analyst@company.org)")
    
    # Rate limiting for edgartools requests
    sec_api_rate_limit: float = Field(default=0.1)  # 10 requests per second max
    
    # Analysis Configuration
    max_report_length: int = Field(default=50000)  # Max characters to analyze
    risk_categories: list[str] = Field(default=[
        "credit_risk",
        "market_risk", 
        "operational_risk",
        "liquidity_risk",
        "regulatory_risk",
        "cybersecurity_risk",
        "climate_risk",
        "reputation_risk"
    ])
    
    # Strands Agents Configuration
    agent_temperature: float = Field(default=0.1)
    agent_max_tokens: int = Field(default=4000)
    
    # Cache Configuration
    cache_enabled: bool = Field(default=True)
    cache_db_path: str = Field(default="sec_analyzer_cache.db")
    cache_expiry_days: int = Field(default=7)  # Cache SEC data for 7 days
    cache_compression: bool = Field(default=True)  # Compress cached content
    cache_max_size_mb: int = Field(default=500)  # Max cache size in MB
    
    class Config:
        env_prefix = "SEC_ANALYZER_"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Override with environment variables if present
        self.aws_region = os.getenv("SEC_ANALYZER_AWS_REGION", self.aws_region)
        self.bedrock_model = os.getenv("SEC_ANALYZER_BEDROCK_MODEL", self.bedrock_model)
        self.user_agent = os.getenv("SEC_ANALYZER_USER_AGENT", self.user_agent)
    
    def get_bedrock_client_config(self) -> dict:
        """Get configuration for AWS Bedrock client."""
        return {
            "region_name": self.aws_region,
            "service_name": "bedrock-runtime"
        }
    
    def get_sec_headers(self) -> dict:
        """Get headers for edgartools requests (if needed)."""
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/json"
        }