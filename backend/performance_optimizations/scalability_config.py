# backend/performance_optimizations/scalability_config.py
"""
Scalability configuration for horizontal and vertical scaling.
Includes load balancing, auto-scaling, and distributed systems optimizations.
"""

import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseSettings
from sqlalchemy.pool import QueuePool
from redis.sentinel import Sentinel

logger = logging.getLogger(__name__)

# ─── SCALING STRATEGIES ────────────────────────────────────────────────────

class ScalingStrategy(Enum):
    VERTICAL = "vertical"      # Scale up (more CPU/RAM)
    HORIZONTAL = "horizontal"  # Scale out (more instances)
    HYBRID = "hybrid"         # Both strategies

@dataclass
class ScalingConfig:
    """Configuration for different scaling scenarios."""
    
    # Database scaling
    db_pool_size: int
    db_max_overflow: int
    db_read_replicas: List[str]
    
    # Redis scaling
    redis_cluster_nodes: List[str]
    redis_sentinel_hosts: List[str]
    
    # Application scaling
    worker_processes: int
    max_concurrent_requests: int
    request_timeout: int
    
    # Auto-scaling triggers
    cpu_threshold: float = 70.0
    memory_threshold: float = 80.0
    response_time_threshold: float = 2.0
    
    # Circuit breaker settings
    failure_threshold: int = 5
    recovery_timeout: int = 60

# Environment-specific scaling configurations
SCALING_CONFIGS = {
    "development": ScalingConfig(
        db_pool_size=5,
        db_max_overflow=10,
        db_read_replicas=[],
        redis_cluster_nodes=[],
        redis_sentinel_hosts=[],
        worker_processes=1,
        max_concurrent_requests=100,
        request_timeout=30,
    ),
    
    "staging": ScalingConfig(
        db_pool_size=10,
        db_max_overflow=20,
        db_read_replicas=["postgresql://read1:5432/db"],
        redis_cluster_nodes=[],
        redis_sentinel_hosts=["redis-sentinel:26379"],
        worker_processes=2,
        max_concurrent_requests=500,
        request_timeout=30,
    ),
    
    "production": ScalingConfig(
        db_pool_size=20,
        db_max_overflow=40,
        db_read_replicas=[
            "postgresql://read1:5432/db",
            "postgresql://read2:5432/db",
            "postgresql://read3:5432/db"
        ],
        redis_cluster_nodes=[
            "redis-cluster-1:6379",
            "redis-cluster-2:6379", 
            "redis-cluster-3:6379"
        ],
        redis_sentinel_hosts=[
            "redis-sentinel-1:26379",
            "redis-sentinel-2:26379",
            "redis-sentinel-3:26379"
        ],
        worker_processes=4,
        max_concurrent_requests=2000,
        request_timeout=60,
        cpu_threshold=60.0,
        memory_threshold=75.0,
        response_time_threshold=1.5,
    )
}

# ─── DATABASE SCALING MANAGER ──────────────────────────────────────────────

class DatabaseScalingManager:
    """Manages database connections and read/write splitting."""
    
    def __init__(self, config: ScalingConfig):
        self.config = config
        self.write_engine = None
        self.read_engines = []
        self._current_read_index = 0
    
    def setup_engines(self, write_dsn: str):
        """Setup write and read database engines."""
        from sqlalchemy.ext.asyncio import create_async_engine
        
        # Write engine with optimized pool
        self.write_engine = create_async_engine(
            write_dsn,
            poolclass=QueuePool,
            pool_size=self.config.db_pool_size,
            max_overflow=self.config.db_max_overflow,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False,
            # Connection arguments for performance
            connect_args={
                "command_timeout": 30,
                "server_settings": {
                    "application_name": "brain2gain_write",
                    "default_transaction_isolation": "read_committed",
                }
            }
        )
        
        # Read replica engines
        for read_dsn in self.config.db_read_replicas:
            read_engine = create_async_engine(
                read_dsn,
                poolclass=QueuePool,
                pool_size=self.config.db_pool_size // 2,  # Smaller pools for reads
                max_overflow=self.config.db_max_overflow // 2,
                pool_timeout=20,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=False,
                connect_args={
                    "command_timeout": 20,
                    "server_settings": {
                        "application_name": "brain2gain_read",
                        "default_transaction_isolation": "read_committed",
                    }
                }
            )
            self.read_engines.append(read_engine)
        
        logger.info(f"Initialized {len(self.read_engines)} read replicas")
    
    def get_read_engine(self):
        """Get read engine with round-robin load balancing."""
        if not self.read_engines:
            return self.write_engine
        
        engine = self.read_engines[self._current_read_index]
        self._current_read_index = (self._current_read_index + 1) % len(self.read_engines)
        return engine
    
    def get_write_engine(self):
        """Get write engine."""
        return self.write_engine


# ─── REDIS SCALING MANAGER ─────────────────────────────────────────────────

class RedisScalingManager:
    """Manages Redis cluster and sentinel connections."""
    
    def __init__(self, config: ScalingConfig):
        self.config = config
        self.cluster_client = None
        self.sentinel_client = None
    
    def setup_redis_cluster(self):
        """Setup Redis cluster for horizontal scaling."""
        if not self.config.redis_cluster_nodes:
            return None
        
        try:
            from redis.cluster import RedisCluster
            
            self.cluster_client = RedisCluster(
                host=self.config.redis_cluster_nodes[0].split(':')[0],
                port=int(self.config.redis_cluster_nodes[0].split(':')[1]),
                decode_responses=True,
                skip_full_coverage_check=True,
                health_check_interval=30,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=100,
            )
            
            logger.info(f"Redis cluster initialized with {len(self.config.redis_cluster_nodes)} nodes")
            return self.cluster_client
            
        except Exception as e:
            logger.error(f"Failed to setup Redis cluster: {e}")
            return None
    
    def setup_redis_sentinel(self):
        """Setup Redis Sentinel for high availability."""
        if not self.config.redis_sentinel_hosts:
            return None
        
        try:
            sentinel_hosts = [
                (host.split(':')[0], int(host.split(':')[1]))
                for host in self.config.redis_sentinel_hosts
            ]
            
            sentinel = Sentinel(sentinel_hosts)
            self.sentinel_client = sentinel.master_for(
                'mymaster',
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            
            logger.info(f"Redis Sentinel initialized with {len(sentinel_hosts)} sentinels")
            return self.sentinel_client
            
        except Exception as e:
            logger.error(f"Failed to setup Redis Sentinel: {e}")
            return None
    
    def get_redis_client(self):
        """Get appropriate Redis client based on configuration."""
        if self.cluster_client:
            return self.cluster_client
        elif self.sentinel_client:
            return self.sentinel_client
        else:
            # Fallback to single Redis instance
            import redis.asyncio as redis
            return redis.from_url("redis://localhost:6379")


# ─── CIRCUIT BREAKER PATTERN ───────────────────────────────────────────────

class CircuitBreakerState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures detected, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker for external service calls."""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        """Call function with circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )


# ─── LOAD BALANCING UTILITIES ──────────────────────────────────────────────

class LoadBalancer:
    """Simple load balancer for multiple service instances."""
    
    def __init__(self, endpoints: List[str]):
        self.endpoints = endpoints
        self.current_index = 0
        self.health_status = {endpoint: True for endpoint in endpoints}
    
    def get_endpoint(self) -> Optional[str]:
        """Get next healthy endpoint using round-robin."""
        healthy_endpoints = [
            ep for ep in self.endpoints 
            if self.health_status.get(ep, False)
        ]
        
        if not healthy_endpoints:
            logger.warning("No healthy endpoints available")
            return None
        
        endpoint = healthy_endpoints[self.current_index % len(healthy_endpoints)]
        self.current_index += 1
        return endpoint
    
    async def health_check(self):
        """Perform health checks on all endpoints."""
        import aiohttp
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for endpoint in self.endpoints:
                try:
                    async with session.get(f"{endpoint}/health") as response:
                        self.health_status[endpoint] = response.status == 200
                except Exception:
                    self.health_status[endpoint] = False
        
        healthy_count = sum(self.health_status.values())
        logger.info(f"Health check completed: {healthy_count}/{len(self.endpoints)} endpoints healthy")


# ─── AUTO-SCALING MONITOR ──────────────────────────────────────────────────

import time
import psutil
import asyncio

class AutoScalingMonitor:
    """Monitor system metrics for auto-scaling decisions."""
    
    def __init__(self, config: ScalingConfig):
        self.config = config
        self.metrics_history = []
        self.last_scale_action = 0
        self.min_scale_interval = 300  # 5 minutes between scaling actions
    
    async def collect_metrics(self) -> Dict:
        """Collect current system metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application-specific metrics (would be collected from your app)
        app_metrics = await self._collect_app_metrics()
        
        metrics = {
            'timestamp': time.time(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'response_time_avg': app_metrics.get('response_time_avg', 0),
            'active_connections': app_metrics.get('active_connections', 0),
            'error_rate': app_metrics.get('error_rate', 0)
        }
        
        # Keep last 100 metrics
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)
        
        return metrics
    
    async def _collect_app_metrics(self) -> Dict:
        """Collect application-specific metrics."""
        # This would integrate with your monitoring system
        return {
            'response_time_avg': 0.5,  # seconds
            'active_connections': 50,
            'error_rate': 0.01  # 1%
        }
    
    def should_scale_up(self) -> bool:
        """Determine if we should scale up."""
        if not self.metrics_history or len(self.metrics_history) < 5:
            return False
        
        # Get recent metrics (last 5 minutes)
        recent_metrics = self.metrics_history[-5:]
        
        # Check if consistently above thresholds
        high_cpu = all(m['cpu_percent'] > self.config.cpu_threshold for m in recent_metrics)
        high_memory = all(m['memory_percent'] > self.config.memory_threshold for m in recent_metrics)
        slow_response = all(m['response_time_avg'] > self.config.response_time_threshold for m in recent_metrics)
        
        return (high_cpu or high_memory or slow_response) and self._can_scale()
    
    def should_scale_down(self) -> bool:
        """Determine if we should scale down."""
        if not self.metrics_history or len(self.metrics_history) < 10:
            return False
        
        # Get recent metrics (last 10 minutes)
        recent_metrics = self.metrics_history[-10:]
        
        # Check if consistently below thresholds (with margin)
        low_cpu = all(m['cpu_percent'] < self.config.cpu_threshold * 0.5 for m in recent_metrics)
        low_memory = all(m['memory_percent'] < self.config.memory_threshold * 0.5 for m in recent_metrics)
        fast_response = all(m['response_time_avg'] < self.config.response_time_threshold * 0.5 for m in recent_metrics)
        
        return low_cpu and low_memory and fast_response and self._can_scale()
    
    def _can_scale(self) -> bool:
        """Check if enough time has passed since last scaling action."""
        return time.time() - self.last_scale_action > self.min_scale_interval
    
    async def trigger_scale_action(self, action: str):
        """Trigger scaling action (would integrate with container orchestrator)."""
        logger.info(f"Triggering scale {action} action")
        
        # Here you would integrate with:
        # - Kubernetes HPA
        # - Docker Swarm
        # - AWS ECS/EKS
        # - Other orchestration platforms
        
        self.last_scale_action = time.time()
        
        # Example Kubernetes scaling
        if action == "up":
            await self._scale_kubernetes_deployment("brain2gain-backend", replicas="+1")
        elif action == "down":
            await self._scale_kubernetes_deployment("brain2gain-backend", replicas="-1")
    
    async def _scale_kubernetes_deployment(self, deployment_name: str, replicas: str):
        """Scale Kubernetes deployment."""
        try:
            # This would use the Kubernetes Python client
            # from kubernetes import client, config
            # 
            # config.load_incluster_config()  # or load_kube_config() for local
            # v1 = client.AppsV1Api()
            # 
            # if replicas.startswith('+'):
            #     current = v1.read_namespaced_deployment(deployment_name, 'default').spec.replicas
            #     new_replicas = current + int(replicas[1:])
            # elif replicas.startswith('-'):
            #     current = v1.read_namespaced_deployment(deployment_name, 'default').spec.replicas
            #     new_replicas = max(1, current - int(replicas[1:]))
            # else:
            #     new_replicas = int(replicas)
            # 
            # v1.patch_namespaced_deployment_scale(
            #     deployment_name, 
            #     'default',
            #     {'spec': {'replicas': new_replicas}}
            # )
            
            logger.info(f"Would scale {deployment_name} to {replicas} replicas")
            
        except Exception as e:
            logger.error(f"Failed to scale deployment {deployment_name}: {e}")


# ─── GLOBAL SCALING MANAGER ────────────────────────────────────────────────

class ScalingManager:
    """Central manager for all scaling operations."""
    
    def __init__(self, environment: str = "development"):
        self.config = SCALING_CONFIGS.get(environment, SCALING_CONFIGS["development"])
        self.db_manager = DatabaseScalingManager(self.config)
        self.redis_manager = RedisScalingManager(self.config)
        self.monitor = AutoScalingMonitor(self.config)
        self.circuit_breakers = {}
    
    async def initialize(self, db_dsn: str):
        """Initialize all scaling components."""
        # Setup database scaling
        self.db_manager.setup_engines(db_dsn)
        
        # Setup Redis scaling
        redis_client = self.redis_manager.setup_redis_cluster()
        if not redis_client:
            redis_client = self.redis_manager.setup_redis_sentinel()
        
        # Start monitoring (in production)
        if self.config.worker_processes > 1:
            asyncio.create_task(self._monitoring_loop())
        
        logger.info(f"Scaling manager initialized for {self.config.worker_processes} workers")
    
    async def _monitoring_loop(self):
        """Main monitoring loop for auto-scaling."""
        while True:
            try:
                metrics = await self.monitor.collect_metrics()
                
                if self.monitor.should_scale_up():
                    await self.monitor.trigger_scale_action("up")
                elif self.monitor.should_scale_down():
                    await self.monitor.trigger_scale_action("down")
                
                # Sleep for 1 minute between checks
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(
                failure_threshold=self.config.failure_threshold,
                recovery_timeout=self.config.recovery_timeout
            )
        return self.circuit_breakers[service_name]


# Export main components
__all__ = [
    'ScalingConfig',
    'ScalingStrategy', 
    'SCALING_CONFIGS',
    'DatabaseScalingManager',
    'RedisScalingManager',
    'CircuitBreaker',
    'LoadBalancer',
    'AutoScalingMonitor',
    'ScalingManager'
]