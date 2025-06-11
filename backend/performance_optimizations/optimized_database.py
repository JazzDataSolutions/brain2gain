# backend/performance_optimizations/optimized_database.py
"""
Optimized database configuration with connection pooling, caching and performance tuning.
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy.engine.events import event
from sqlalchemy import text
from app.core.config import settings

logger = logging.getLogger(__name__)

# ─── OPTIMIZED ENGINE CONFIGURATION ───────────────────────────────────────

def create_optimized_engine():
    """Create database engine with optimized settings."""
    
    # Connection pool configuration based on environment
    if settings.ENVIRONMENT == "production":
        pool_settings = {
            "poolclass": QueuePool,
            "pool_size": 20,  # Number of persistent connections
            "max_overflow": 30,  # Additional connections when pool is full
            "pool_timeout": 30,  # Timeout to get connection from pool
            "pool_recycle": 3600,  # Recycle connections every hour
            "pool_pre_ping": True,  # Validate connections before use
        }
    else:
        # Development settings
        pool_settings = {
            "poolclass": StaticPool,
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 10,
            "pool_recycle": 1800,
            "pool_pre_ping": True,
        }
    
    engine = create_async_engine(
        str(settings.SQLALCHEMY_DATABASE_URI),
        echo=settings.ENVIRONMENT == "local",  # SQL logging only in development
        future=True,
        # Connection pool settings
        **pool_settings,
        # Performance optimizations
        connect_args={
            "command_timeout": 30,
            "server_settings": {
                "application_name": "brain2gain_app",
                "jit": "off",  # Disable JIT for faster simple queries
            },
        },
    )
    
    # Add connection event listeners for optimization
    _setup_connection_events(engine)
    
    return engine


def _setup_connection_events(engine):
    """Setup connection-level optimizations."""
    
    @event.listens_for(engine.sync_engine, "connect")
    def set_connection_settings(dbapi_connection, connection_record):
        """Optimize individual connection settings."""
        with dbapi_connection.cursor() as cursor:
            # Set connection-level optimizations
            cursor.execute("SET statement_timeout = '30s'")  # Prevent runaway queries
            cursor.execute("SET lock_timeout = '10s'")  # Prevent deadlocks
            cursor.execute("SET idle_in_transaction_session_timeout = '5min'")
            cursor.execute("SET tcp_keepalives_idle = 600")  # Keep connections alive
            cursor.execute("SET tcp_keepalives_interval = 30")
            cursor.execute("SET tcp_keepalives_count = 3")
            
            # Optimize for read-heavy workloads
            cursor.execute("SET default_statistics_target = 100")
            cursor.execute("SET random_page_cost = 1.1")  # Assuming SSD storage
            cursor.execute("SET effective_cache_size = '1GB'")  # Adjust based on server RAM


# ─── SESSION MANAGEMENT ───────────────────────────────────────────────────

# Create optimized engine
engine = create_optimized_engine()

# Session factory with optimizations
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent automatic expiry for better performance
    autoflush=True,  # Auto-flush for consistency
    autocommit=False,
)


class DatabaseSession:
    """Enhanced database session with monitoring and optimization."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._query_count = 0
        self._start_time = None
    
    async def __aenter__(self):
        self._start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self._start_time if self._start_time else 0
        
        # Log slow sessions
        if duration > 1.0:  # Warn about sessions taking > 1 second
            logger.warning(
                f"Slow database session: {duration:.2f}s, queries: {self._query_count}"
            )
        
        try:
            if exc_type:
                await self.session.rollback()
            await self.session.close()
        except Exception as e:
            logger.error(f"Error closing database session: {e}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with connection monitoring."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def get_optimized_db() -> AsyncGenerator[DatabaseSession, None]:
    """Get enhanced database session with monitoring."""
    async with AsyncSessionLocal() as session:
        db_session = DatabaseSession(session)
        try:
            async with db_session:
                yield db_session
        except Exception as e:
            logger.error(f"Optimized database session error: {e}")
            raise


# ─── QUERY OPTIMIZATION UTILITIES ─────────────────────────────────────────

class QueryOptimizer:
    """Utilities for query optimization and monitoring."""
    
    @staticmethod
    async def explain_query(session: AsyncSession, query: str) -> dict:
        """Get query execution plan for optimization."""
        try:
            result = await session.execute(
                text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
            )
            return result.scalar()
        except Exception as e:
            logger.error(f"Error explaining query: {e}")
            return {}
    
    @staticmethod
    async def get_slow_queries(session: AsyncSession, limit: int = 10) -> list:
        """Get slowest queries from pg_stat_statements."""
        query = """
        SELECT 
            query,
            calls,
            total_time,
            mean_time,
            max_time,
            rows
        FROM pg_stat_statements 
        WHERE query NOT LIKE '%pg_stat_statements%'
        ORDER BY mean_time DESC 
        LIMIT :limit
        """
        try:
            result = await session.execute(text(query), {"limit": limit})
            return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not fetch slow queries: {e}")
            return []
    
    @staticmethod
    async def get_table_stats(session: AsyncSession) -> dict:
        """Get table statistics for optimization insights."""
        query = """
        SELECT 
            schemaname,
            tablename,
            n_tup_ins as inserts,
            n_tup_upd as updates,
            n_tup_del as deletes,
            n_live_tup as live_tuples,
            n_dead_tup as dead_tuples,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC
        """
        try:
            result = await session.execute(text(query))
            return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not fetch table stats: {e}")
            return {}


# ─── CONNECTION MONITORING ────────────────────────────────────────────────

import time
import asyncio
from contextlib import asynccontextmanager

class ConnectionMonitor:
    """Monitor database connections and performance."""
    
    def __init__(self):
        self.active_connections = 0
        self.total_queries = 0
        self.slow_queries = 0
        self.connection_errors = 0
    
    @asynccontextmanager
    async def monitor_connection(self):
        """Context manager to monitor connection usage."""
        self.active_connections += 1
        start_time = time.time()
        
        try:
            yield
        except Exception as e:
            self.connection_errors += 1
            logger.error(f"Connection error: {e}")
            raise
        finally:
            self.active_connections -= 1
            duration = time.time() - start_time
            
            if duration > 5.0:  # Log connections lasting > 5 seconds
                logger.warning(f"Long-running connection: {duration:.2f}s")
    
    async def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "active_connections": self.active_connections,
            "total_queries": self.total_queries,
            "slow_queries": self.slow_queries,
            "connection_errors": self.connection_errors,
            "error_rate": self.connection_errors / max(1, self.total_queries) * 100
        }


# Global monitor instance
connection_monitor = ConnectionMonitor()


# ─── HEALTH CHECK UTILITIES ───────────────────────────────────────────────

async def check_database_health() -> dict:
    """Comprehensive database health check."""
    try:
        async with AsyncSessionLocal() as session:
            # Test basic connectivity
            await session.execute(text("SELECT 1"))
            
            # Check connection pool status
            pool = engine.pool
            pool_status = {
                "size": pool.size() if hasattr(pool, 'size') else 0,
                "checked_in": pool.checkedin() if hasattr(pool, 'checkedin') else 0,
                "checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else 0,
                "invalid": pool.invalid() if hasattr(pool, 'invalid') else 0,
            }
            
            # Check for long-running queries
            long_queries = await session.execute(text("""
                SELECT COUNT(*) as count 
                FROM pg_stat_activity 
                WHERE state = 'active' 
                AND query_start < NOW() - INTERVAL '1 minute'
                AND query NOT LIKE '%pg_stat_activity%'
            """))
            
            return {
                "status": "healthy",
                "pool": pool_status,
                "long_running_queries": long_queries.scalar(),
                "monitor_stats": await connection_monitor.get_stats()
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "monitor_stats": await connection_monitor.get_stats()
        }


# ─── MIGRATION UTILITIES ──────────────────────────────────────────────────

async def create_performance_indexes():
    """Create additional performance indexes via raw SQL."""
    indexes = [
        # Full-text search indexes
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_product_name_gin 
        ON product USING gin(to_tsvector('english', name))
        """,
        
        # Partial indexes for active records
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_product_active 
        ON product (created_at, unit_price) 
        WHERE status = 'ACTIVE'
        """,
        
        # Composite indexes for common filters
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_order_customer_status_date 
        ON salesorder (customer_id, status, order_date DESC)
        """,
        
        # Expression indexes for computed values
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customer_name_lower 
        ON customer (lower(first_name || ' ' || last_name))
        """,
    ]
    
    async with AsyncSessionLocal() as session:
        for index_sql in indexes:
            try:
                await session.execute(text(index_sql))
                logger.info(f"Created index: {index_sql.split('IF NOT EXISTS')[1].split('ON')[0].strip()}")
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")


# Export optimized components
__all__ = [
    'engine',
    'AsyncSessionLocal', 
    'get_db',
    'get_optimized_db',
    'DatabaseSession',
    'QueryOptimizer',
    'ConnectionMonitor',
    'connection_monitor',
    'check_database_health',
    'create_performance_indexes'
]