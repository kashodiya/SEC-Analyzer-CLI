"""SEC EDGAR API client for fetching company filings using edgartools."""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import time
import hashlib

from edgar import Company, Filing, get_filings, set_identity

from .config import Config
from .cache_manager import CacheManager


class SECClient:
    """Client for interacting with SEC EDGAR API using edgartools."""
    
    def __init__(self, config: Config):
        self.config = config
        self.cache = CacheManager(config)
        # Set user agent for edgartools - this is required
        set_identity(config.user_agent)
    
    async def initialize(self):
        """Initialize the SEC client and cache."""
        await self.cache.initialize()
    
    async def get_company_cik(self, ticker: str) -> Optional[str]:
        """Get CIK (Central Index Key) for a company ticker using edgartools."""
        # Try cache first
        cached_cik = await self.cache.get_company_cik(ticker)
        if cached_cik:
            return cached_cik
        
        try:
            # Use edgartools to get company
            company = Company(ticker)
            if company and hasattr(company, 'cik'):
                cik = str(company.cik).zfill(10)
                # Cache the result
                await self.cache.cache_company_cik(ticker, cik)
                return cik
            return None
        except Exception as e:
            raise Exception(f"Error fetching CIK for {ticker}: {e}")
    
    async def get_company_reports(self, ticker: str, report_type: str = '10-K') -> List[Dict]:
        """Fetch SEC reports for a company using edgartools."""
        # Try cache first
        cached_reports = await self.cache.get_filing_metadata(ticker, report_type)
        if cached_reports:
            return cached_reports
        
        try:
            # Get company using edgartools
            company = Company(ticker)
            if not company:
                raise Exception(f"Could not find company for ticker {ticker}")
            
            # Get filings of specified type with error handling
            try:
                if report_type == 'all':
                    filings = company.get_filings()
                else:
                    filings = company.get_filings(form=report_type)
            except Exception as e:
                # If there's an issue with get_filings, try alternative approach
                print(f"Warning: Error with get_filings: {e}")
                # Try using the global get_filings function instead
                from edgar import get_filings
                try:
                    if report_type == 'all':
                        filings = get_filings(ticker=ticker)
                    else:
                        filings = get_filings(ticker=ticker, form=report_type)
                except Exception as e2:
                    raise Exception(f"Could not fetch filings using alternative method: {e2}")
            
            reports = []
            filing_count = 0
            max_filings = 3
            
            # Convert filings to list if it's not already
            if hasattr(filings, '__iter__'):
                filings_list = list(filings)
            else:
                filings_list = [filings]
            
            for filing in filings_list:
                if filing_count >= max_filings:
                    break
                    
                try:
                    # Get filing content
                    content = self._extract_filing_content(filing)
                    
                    # Handle potential pyarrow issues by converting attributes safely
                    filing_date = None
                    if hasattr(filing, 'filing_date'):
                        try:
                            if hasattr(filing.filing_date, 'as_py'):
                                filing_date = filing.filing_date.as_py().strftime('%Y-%m-%d')
                            elif hasattr(filing.filing_date, 'strftime'):
                                filing_date = filing.filing_date.strftime('%Y-%m-%d')
                            else:
                                filing_date = str(filing.filing_date)
                        except Exception:
                            filing_date = str(filing.filing_date) if filing.filing_date else None
                    
                    # Safely get form type
                    form_type = getattr(filing, 'form', report_type)
                    if hasattr(form_type, 'as_py'):
                        try:
                            form_type = form_type.as_py()
                        except Exception:
                            form_type = str(form_type)
                    
                    # Safely get accession number
                    accession_number = getattr(filing, 'accession_number', '')
                    if hasattr(accession_number, 'as_py'):
                        try:
                            accession_number = accession_number.as_py()
                        except Exception:
                            accession_number = str(accession_number)
                    
                    report = {
                        'ticker': ticker.upper(),
                        'cik': str(company.cik).zfill(10) if hasattr(company, 'cik') else '',
                        'form_type': str(form_type),
                        'filing_date': filing_date,
                        'accession_number': str(accession_number),
                        'primary_document': str(getattr(filing, 'primary_document', '')),
                        'content': content
                    }
                    reports.append(report)
                    filing_count += 1
                    
                except Exception as e:
                    # Continue with other filings if one fails
                    print(f"Error processing filing: {e}")
                    continue
            
            if not reports:
                raise Exception(f"No valid filings found for {ticker}")
            
            # Cache the reports
            await self.cache.cache_filing_metadata(ticker, report_type, reports)
            return reports
            
        except Exception as e:
            raise Exception(f"Error fetching reports for {ticker}: {e}")
    
    def _extract_filing_content(self, filing: Filing) -> str:
        """Extract meaningful content from a filing."""
        try:
            # Try to get the text content
            if hasattr(filing, 'text') and callable(filing.text):
                content = filing.text()
                if content:
                    # Limit content length
                    return content[:self.config.max_report_length]
            
            # Fallback to HTML content if available
            if hasattr(filing, 'html') and callable(filing.html):
                html_content = filing.html()
                if html_content:
                    # Simple text extraction from HTML
                    import re
                    text = re.sub(r'<[^>]+>', ' ', str(html_content))
                    text = re.sub(r'\s+', ' ', text).strip()
                    return text[:self.config.max_report_length]
            
            # If no content available, return basic info
            return f"Filing {filing.form} for {filing.accession_number} - Content extraction not available"
            
        except Exception as e:
            return f"Error extracting content from filing: {e}"
    
    async def get_recent_filings(self, ticker: str, limit: int = 5) -> List[Dict]:
        """Get recent filings for a company using edgartools."""
        try:
            company = Company(ticker)
            if not company:
                raise Exception(f"Could not find company for ticker {ticker}")
            
            filings = company.get_filings()
            
            results = []
            filing_count = 0
            
            # Convert filings to list if it's not already
            if hasattr(filings, '__iter__'):
                filings_list = list(filings)
            else:
                filings_list = [filings]
            
            for filing in filings_list:
                if filing_count >= limit:
                    break
                    
                try:
                    # Handle potential pyarrow issues
                    filing_date = None
                    if hasattr(filing, 'filing_date'):
                        try:
                            if hasattr(filing.filing_date, 'as_py'):
                                filing_date = filing.filing_date.as_py().strftime('%Y-%m-%d')
                            elif hasattr(filing.filing_date, 'strftime'):
                                filing_date = filing.filing_date.strftime('%Y-%m-%d')
                            else:
                                filing_date = str(filing.filing_date)
                        except Exception:
                            filing_date = str(filing.filing_date) if filing.filing_date else None
                    
                    # Safely get form type
                    form_type = getattr(filing, 'form', '')
                    if hasattr(form_type, 'as_py'):
                        try:
                            form_type = form_type.as_py()
                        except Exception:
                            form_type = str(form_type)
                    
                    # Safely get accession number
                    accession_number = getattr(filing, 'accession_number', '')
                    if hasattr(accession_number, 'as_py'):
                        try:
                            accession_number = accession_number.as_py()
                        except Exception:
                            accession_number = str(accession_number)
                    
                    results.append({
                        'date': filing_date,
                        'form_type': str(form_type),
                        'description': f"{form_type} Filing",
                        'url': str(getattr(filing, 'filing_details_url', '')),
                        'accession_number': str(accession_number)
                    })
                    filing_count += 1
                    
                except Exception as e:
                    print(f"Error processing filing: {e}")
                    continue
            
            return results
            
        except Exception as e:
            raise Exception(f"Error fetching filings for {ticker}: {e}")
    
    async def get_company_facts(self, ticker: str) -> Dict:
        """Get company facts using edgartools."""
        try:
            company = Company(ticker)
            if not company:
                raise Exception(f"Could not find company for ticker {ticker}")
            
            # Get company facts if available
            if hasattr(company, 'get_facts'):
                facts = company.get_facts()
                return facts
            
            # Fallback to basic company info
            return {
                'name': getattr(company, 'name', ''),
                'cik': str(company.cik).zfill(10) if hasattr(company, 'cik') else '',
                'ticker': ticker.upper(),
                'sic': getattr(company, 'sic', ''),
                'industry': getattr(company, 'industry', '')
            }
            
        except Exception as e:
            raise Exception(f"Error fetching company facts for {ticker}: {e}")