"""SQLite cache manager for SEC data."""

import aiosqlite
import json
import hashlib
import gzip
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

from .config import Config


class CacheManager:
    """Manages SQLite cache for SEC data to avoid repeated downloads."""
    
    def __init__(self, config: Config):
        self.config = config
        self.db_path = config.cache_db_path
        self.cache_enabled = config.cache_enabled
        self.expiry_days = config.cache_expiry_days
        self.compression_enabled = config.cache_compression
        self.max_cache_size_mb = config.cache_max_size_mb
        self.cache_hits = 0
        self.cache_misses = 0
        
    async def initialize(self):
        """Initialize the cache database with required tables."""
        if not self.cache_enabled:
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            # Check if we need to migrate the schema
            await self._migrate_schema(db)
            
            # Company CIK cache table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS company_ciks (
                    ticker TEXT PRIMARY KEY,
                    cik TEXT NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # SEC filings metadata cache
            await db.execute("""
                CREATE TABLE IF NOT EXISTS filing_metadata (
                    ticker TEXT,
                    report_type TEXT,
                    data_hash TEXT,
                    metadata_json TEXT NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (ticker, report_type, data_hash)
                )
            """)
            
            # SEC document content cache with compression support
            await db.execute("""
                CREATE TABLE IF NOT EXISTS document_content (
                    cik TEXT,
                    accession_number TEXT,
                    primary_document TEXT,
                    content BLOB NOT NULL,
                    content_length INTEGER,
                    is_compressed BOOLEAN DEFAULT FALSE,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (cik, accession_number, primary_document)
                )
            """)
            
            # Analysis results cache with compression
            await db.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    ticker TEXT,
                    report_type TEXT,
                    content_hash TEXT,
                    analysis_json BLOB NOT NULL,
                    is_compressed BOOLEAN DEFAULT FALSE,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (ticker, report_type, content_hash)
                )
            """)
            
            # Cache performance tracking table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cache_performance (
                    operation TEXT,
                    cache_hits INTEGER DEFAULT 0,
                    cache_misses INTEGER DEFAULT 0,
                    total_requests INTEGER DEFAULT 0,
                    avg_response_time_ms REAL DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (operation)
                )
            """)
            
            # Create indexes for better performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_filing_metadata_ticker ON filing_metadata(ticker)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_document_content_cik ON document_content(cik)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_analysis_ticker ON analysis_results(ticker)")
            
            # Only create these indexes if the columns exist
            try:
                await db.execute("CREATE INDEX IF NOT EXISTS idx_document_content_accessed ON document_content(last_accessed)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_analysis_accessed ON analysis_results(last_accessed)")
            except:
                pass  # Columns don't exist yet, will be added in migration
            
            await db.commit()
    
    async def _migrate_schema(self, db):
        """Migrate database schema to latest version."""
        try:
            # Check if we need to add new columns to existing tables
            cursor = await db.execute("PRAGMA table_info(document_content)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Add missing columns to document_content
            if 'is_compressed' not in column_names:
                await db.execute("ALTER TABLE document_content ADD COLUMN is_compressed BOOLEAN DEFAULT FALSE")
            if 'access_count' not in column_names:
                await db.execute("ALTER TABLE document_content ADD COLUMN access_count INTEGER DEFAULT 1")
            if 'last_accessed' not in column_names:
                await db.execute("ALTER TABLE document_content ADD COLUMN last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            # Check analysis_results table
            cursor = await db.execute("PRAGMA table_info(analysis_results)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Add missing columns to analysis_results
            if 'is_compressed' not in column_names:
                await db.execute("ALTER TABLE analysis_results ADD COLUMN is_compressed BOOLEAN DEFAULT FALSE")
            if 'access_count' not in column_names:
                await db.execute("ALTER TABLE analysis_results ADD COLUMN access_count INTEGER DEFAULT 1")
            if 'last_accessed' not in column_names:
                await db.execute("ALTER TABLE analysis_results ADD COLUMN last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            await db.commit()
            
        except Exception:
            # If migration fails, continue - the tables will be created fresh
            pass
    
    def _is_expired(self, cached_at: str) -> bool:
        """Check if cached data is expired."""
        try:
            cached_time = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
            expiry_time = cached_time + timedelta(days=self.expiry_days)
            return datetime.now() > expiry_time
        except:
            return True  # If we can't parse the date, consider it expired
    
    def _generate_hash(self, data: str) -> str:
        """Generate hash for data to detect changes."""
        return hashlib.md5(data.encode()).hexdigest()
    
    def _compress_data(self, data: str) -> bytes:
        """Compress data if compression is enabled."""
        if self.compression_enabled:
            return gzip.compress(data.encode('utf-8'))
        return data.encode('utf-8')
    
    def _decompress_data(self, data: bytes, is_compressed: bool) -> str:
        """Decompress data if it was compressed."""
        if is_compressed and self.compression_enabled:
            return gzip.decompress(data).decode('utf-8')
        return data.decode('utf-8')
    
    async def _update_performance_stats(self, operation: str, is_hit: bool, response_time_ms: float):
        """Update cache performance statistics."""
        if not self.cache_enabled:
            return
            
        async with aiosqlite.connect(self.db_path) as db:
            # Get current stats
            cursor = await db.execute(
                "SELECT cache_hits, cache_misses, total_requests, avg_response_time_ms FROM cache_performance WHERE operation = ?",
                (operation,)
            )
            row = await cursor.fetchone()
            
            if row:
                hits, misses, total, avg_time = row
                if is_hit:
                    hits += 1
                else:
                    misses += 1
                total += 1
                # Update running average
                avg_time = ((avg_time * (total - 1)) + response_time_ms) / total
                
                await db.execute(
                    "UPDATE cache_performance SET cache_hits = ?, cache_misses = ?, total_requests = ?, avg_response_time_ms = ?, last_updated = CURRENT_TIMESTAMP WHERE operation = ?",
                    (hits, misses, total, avg_time, operation)
                )
            else:
                # First entry for this operation
                hits = 1 if is_hit else 0
                misses = 0 if is_hit else 1
                await db.execute(
                    "INSERT INTO cache_performance (operation, cache_hits, cache_misses, total_requests, avg_response_time_ms) VALUES (?, ?, ?, 1, ?)",
                    (operation, hits, misses, response_time_ms)
                )
            
            await db.commit()
    
    async def get_company_cik(self, ticker: str) -> Optional[str]:
        """Get cached CIK for a company ticker."""
        if not self.cache_enabled:
            return None
        
        start_time = time.time()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT cik, cached_at FROM company_ciks WHERE ticker = ?",
                (ticker.upper(),)
            )
            row = await cursor.fetchone()
            
            response_time = (time.time() - start_time) * 1000
            
            if row and not self._is_expired(row[1]):
                await self._update_performance_stats("company_cik", True, response_time)
                self.cache_hits += 1
                return row[0]
            
            await self._update_performance_stats("company_cik", False, response_time)
            self.cache_misses += 1
        
        return None
    
    async def cache_company_cik(self, ticker: str, cik: str):
        """Cache CIK for a company ticker."""
        if not self.cache_enabled:
            return
            
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO company_ciks (ticker, cik) VALUES (?, ?)",
                (ticker.upper(), cik)
            )
            await db.commit()
    
    async def get_filing_metadata(self, ticker: str, report_type: str) -> Optional[List[Dict]]:
        """Get cached filing metadata for a company and report type."""
        if not self.cache_enabled:
            return None
            
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT metadata_json, cached_at FROM filing_metadata WHERE ticker = ? AND report_type = ? ORDER BY cached_at DESC LIMIT 1",
                (ticker.upper(), report_type)
            )
            row = await cursor.fetchone()
            
            if row and not self._is_expired(row[1]):
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    pass
        
        return None
    
    async def cache_filing_metadata(self, ticker: str, report_type: str, metadata: List[Dict]):
        """Cache filing metadata for a company and report type."""
        if not self.cache_enabled:
            return
            
        metadata_json = json.dumps(metadata, default=str)
        data_hash = self._generate_hash(metadata_json)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO filing_metadata (ticker, report_type, data_hash, metadata_json) VALUES (?, ?, ?, ?)",
                (ticker.upper(), report_type, data_hash, metadata_json)
            )
            await db.commit()
    
    async def get_document_content(self, cik: str, accession_number: str, primary_document: str) -> Optional[str]:
        """Get cached document content."""
        if not self.cache_enabled:
            return None
        
        start_time = time.time()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT content, is_compressed, cached_at FROM document_content WHERE cik = ? AND accession_number = ? AND primary_document = ?",
                (cik, accession_number, primary_document)
            )
            row = await cursor.fetchone()
            
            response_time = (time.time() - start_time) * 1000
            
            if row and not self._is_expired(row[2]):
                # Update access statistics
                await db.execute(
                    "UPDATE document_content SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE cik = ? AND accession_number = ? AND primary_document = ?",
                    (cik, accession_number, primary_document)
                )
                await db.commit()
                
                await self._update_performance_stats("document_content", True, response_time)
                self.cache_hits += 1
                return self._decompress_data(row[0], row[1])
            
            await self._update_performance_stats("document_content", False, response_time)
            self.cache_misses += 1
        
        return None
    
    async def cache_document_content(self, cik: str, accession_number: str, primary_document: str, content: str):
        """Cache document content with compression."""
        if not self.cache_enabled:
            return
        
        # Check cache size limit
        await self._enforce_cache_size_limit()
        
        compressed_content = self._compress_data(content)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO document_content (cik, accession_number, primary_document, content, content_length, is_compressed) VALUES (?, ?, ?, ?, ?, ?)",
                (cik, accession_number, primary_document, compressed_content, len(content), self.compression_enabled)
            )
            await db.commit()
    
    async def get_analysis_results(self, ticker: str, report_type: str, content_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis results."""
        if not self.cache_enabled:
            return None
        
        start_time = time.time()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT analysis_json, is_compressed, cached_at FROM analysis_results WHERE ticker = ? AND report_type = ? AND content_hash = ?",
                (ticker.upper(), report_type, content_hash)
            )
            row = await cursor.fetchone()
            
            response_time = (time.time() - start_time) * 1000
            
            if row and not self._is_expired(row[2]):
                # Update access statistics
                await db.execute(
                    "UPDATE analysis_results SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE ticker = ? AND report_type = ? AND content_hash = ?",
                    (ticker.upper(), report_type, content_hash)
                )
                await db.commit()
                
                await self._update_performance_stats("analysis_results", True, response_time)
                self.cache_hits += 1
                
                try:
                    decompressed = self._decompress_data(row[0], row[1])
                    return json.loads(decompressed)
                except (json.JSONDecodeError, Exception):
                    pass
            
            await self._update_performance_stats("analysis_results", False, response_time)
            self.cache_misses += 1
        
        return None
    
    async def cache_analysis_results(self, ticker: str, report_type: str, content_hash: str, analysis: Dict[str, Any]):
        """Cache analysis results with compression."""
        if not self.cache_enabled:
            return
        
        # Check cache size limit
        await self._enforce_cache_size_limit()
        
        analysis_json = json.dumps(analysis, default=str)
        compressed_analysis = self._compress_data(analysis_json)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO analysis_results (ticker, report_type, content_hash, analysis_json, is_compressed) VALUES (?, ?, ?, ?, ?)",
                (ticker.upper(), report_type, content_hash, compressed_analysis, self.compression_enabled)
            )
            await db.commit()
    
    async def cleanup_expired_cache(self):
        """Remove expired cache entries."""
        if not self.cache_enabled:
            return
            
        expiry_date = datetime.now() - timedelta(days=self.expiry_days)
        expiry_str = expiry_date.isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Clean up expired entries
            await db.execute("DELETE FROM company_ciks WHERE cached_at < ?", (expiry_str,))
            await db.execute("DELETE FROM filing_metadata WHERE cached_at < ?", (expiry_str,))
            await db.execute("DELETE FROM document_content WHERE cached_at < ?", (expiry_str,))
            await db.execute("DELETE FROM analysis_results WHERE cached_at < ?", (expiry_str,))
            
            # Vacuum to reclaim space
            await db.execute("VACUUM")
            await db.commit()
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.cache_enabled:
            return {"cache_enabled": False}
            
        async with aiosqlite.connect(self.db_path) as db:
            stats = {"cache_enabled": True}
            
            # Count entries in each table
            for table in ["company_ciks", "filing_metadata", "document_content", "analysis_results"]:
                cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                count = await cursor.fetchone()
                stats[f"{table}_count"] = count[0] if count else 0
            
            # Get database file size
            try:
                db_path = Path(self.db_path)
                if db_path.exists():
                    stats["db_size_mb"] = round(db_path.stat().st_size / (1024 * 1024), 2)
                else:
                    stats["db_size_mb"] = 0
            except:
                stats["db_size_mb"] = "unknown"
            
            # Get oldest and newest cache entries
            cursor = await db.execute("SELECT MIN(cached_at), MAX(cached_at) FROM company_ciks")
            row = await cursor.fetchone()
            if row and row[0]:
                stats["oldest_entry"] = row[0]
                stats["newest_entry"] = row[1]
            
            return stats
    
    async def _enforce_cache_size_limit(self):
        """Enforce cache size limits by removing least recently used items."""
        if not self.cache_enabled:
            return
        
        try:
            db_path = Path(self.db_path)
            if db_path.exists():
                current_size_mb = db_path.stat().st_size / (1024 * 1024)
                
                if current_size_mb > self.max_cache_size_mb:
                    async with aiosqlite.connect(self.db_path) as db:
                        # Remove least recently accessed document content
                        await db.execute(
                            "DELETE FROM document_content WHERE rowid IN (SELECT rowid FROM document_content ORDER BY last_accessed ASC LIMIT 10)"
                        )
                        
                        # Remove least recently accessed analysis results
                        await db.execute(
                            "DELETE FROM analysis_results WHERE rowid IN (SELECT rowid FROM analysis_results ORDER BY last_accessed ASC LIMIT 5)"
                        )
                        
                        await db.commit()
        except Exception:
            pass  # Ignore errors in cache management
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get detailed cache performance statistics."""
        if not self.cache_enabled:
            return {"cache_enabled": False}
        
        async with aiosqlite.connect(self.db_path) as db:
            stats = {"cache_enabled": True}
            
            # Get performance data
            cursor = await db.execute("SELECT * FROM cache_performance")
            perf_data = await cursor.fetchall()
            
            performance = {}
            total_hits = 0
            total_misses = 0
            
            for row in perf_data:
                operation, hits, misses, total, avg_time, last_updated = row
                performance[operation] = {
                    "hits": hits,
                    "misses": misses,
                    "total_requests": total,
                    "hit_rate": round((hits / total * 100) if total > 0 else 0, 2),
                    "avg_response_time_ms": round(avg_time, 2),
                    "last_updated": last_updated
                }
                total_hits += hits
                total_misses += misses
            
            stats["performance"] = performance
            stats["overall_hit_rate"] = round((total_hits / (total_hits + total_misses) * 100) if (total_hits + total_misses) > 0 else 0, 2)
            stats["session_hits"] = self.cache_hits
            stats["session_misses"] = self.cache_misses
            
            return stats
    
    async def clear_cache(self, table: Optional[str] = None):
        """Clear cache data."""
        if not self.cache_enabled:
            return
            
        async with aiosqlite.connect(self.db_path) as db:
            if table:
                await db.execute(f"DELETE FROM {table}")
            else:
                # Clear all tables
                for table_name in ["company_ciks", "filing_metadata", "document_content", "analysis_results", "cache_performance"]:
                    await db.execute(f"DELETE FROM {table_name}")
            
            await db.commit()