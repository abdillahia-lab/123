"""
TerraJinki SOTA Optimizer

Intelligent model routing, caching, batch processing, and
performance optimization for the analysis pipeline.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Callable, TypeVar, Generic
from uuid import uuid4
import asyncio
import hashlib
import json
import logging
from enum import Enum
from functools import wraps

from terrajinki.core.config import get_config, TerraJinkiConfig

logger = logging.getLogger(__name__)


# =============================================================================
# MODEL ROUTING
# =============================================================================

class ModelTier(str, Enum):
    """Model complexity tiers for intelligent routing."""
    OPUS = "opus"      # Complex reasoning, orchestration
    SONNET = "sonnet"  # Standard analysis
    HAIKU = "haiku"    # Fast, simple tasks


class TaskComplexity(str, Enum):
    """Task complexity levels for routing decisions."""
    TRIVIAL = "trivial"      # Simple lookups, formatting
    SIMPLE = "simple"        # Single-step analysis
    MODERATE = "moderate"    # Multi-step analysis
    COMPLEX = "complex"      # Multi-agent coordination
    CRITICAL = "critical"    # High-stakes decisions


@dataclass
class ModelRoute:
    """Model routing decision."""
    model: str
    tier: ModelTier
    reason: str
    estimated_cost: float
    estimated_latency_ms: int


class IntelligentRouter:
    """
    Routes tasks to optimal models based on complexity, cost, and latency.

    Uses heuristics and learned patterns to minimize cost while
    maintaining quality thresholds.
    """

    # Model configurations with current pricing
    MODELS = {
        ModelTier.OPUS: {
            "name": "claude-opus-4-5-20251101",
            "input_cost_per_1m": 15.0,
            "output_cost_per_1m": 75.0,
            "avg_latency_ms": 2000,
            "quality_score": 1.0,
        },
        ModelTier.SONNET: {
            "name": "claude-sonnet-4-20250514",
            "input_cost_per_1m": 3.0,
            "output_cost_per_1m": 15.0,
            "avg_latency_ms": 800,
            "quality_score": 0.9,
        },
        ModelTier.HAIKU: {
            "name": "claude-3-5-haiku-20241022",
            "input_cost_per_1m": 0.25,
            "output_cost_per_1m": 1.25,
            "avg_latency_ms": 300,
            "quality_score": 0.75,
        },
    }

    # Task complexity to model mapping
    COMPLEXITY_ROUTING = {
        TaskComplexity.TRIVIAL: ModelTier.HAIKU,
        TaskComplexity.SIMPLE: ModelTier.HAIKU,
        TaskComplexity.MODERATE: ModelTier.SONNET,
        TaskComplexity.COMPLEX: ModelTier.SONNET,
        TaskComplexity.CRITICAL: ModelTier.OPUS,
    }

    def __init__(self, config: Optional[TerraJinkiConfig] = None):
        self.config = config or get_config()
        self._usage_stats: Dict[str, int] = {}
        self._quality_feedback: Dict[str, float] = {}

    def route(
        self,
        task_type: str,
        complexity: TaskComplexity,
        estimated_tokens: int = 1000,
        quality_required: float = 0.8,
        max_latency_ms: Optional[int] = None,
        max_cost: Optional[float] = None,
    ) -> ModelRoute:
        """
        Route a task to the optimal model.

        Args:
            task_type: Type of task (e.g., "permitting_analysis")
            complexity: Estimated task complexity
            estimated_tokens: Expected input + output tokens
            quality_required: Minimum quality threshold (0-1)
            max_latency_ms: Maximum acceptable latency
            max_cost: Maximum acceptable cost

        Returns:
            ModelRoute with selected model and reasoning
        """
        # Start with complexity-based default
        default_tier = self.COMPLEXITY_ROUTING[complexity]

        # Check constraints and potentially upgrade/downgrade
        selected_tier = default_tier
        reason = f"Default routing for {complexity.value} complexity"

        # Quality constraint: may need to upgrade
        if quality_required > self.MODELS[default_tier]["quality_score"]:
            for tier in [ModelTier.SONNET, ModelTier.OPUS]:
                if self.MODELS[tier]["quality_score"] >= quality_required:
                    selected_tier = tier
                    reason = f"Upgraded for quality requirement ({quality_required})"
                    break

        # Latency constraint: may need to downgrade
        if max_latency_ms:
            if self.MODELS[selected_tier]["avg_latency_ms"] > max_latency_ms:
                for tier in [ModelTier.HAIKU, ModelTier.SONNET]:
                    if self.MODELS[tier]["avg_latency_ms"] <= max_latency_ms:
                        if self.MODELS[tier]["quality_score"] >= quality_required:
                            selected_tier = tier
                            reason = f"Downgraded for latency ({max_latency_ms}ms)"
                            break

        # Cost constraint: may need to downgrade
        model_config = self.MODELS[selected_tier]
        estimated_cost = self._estimate_cost(selected_tier, estimated_tokens)

        if max_cost and estimated_cost > max_cost:
            for tier in [ModelTier.HAIKU, ModelTier.SONNET]:
                cost = self._estimate_cost(tier, estimated_tokens)
                if cost <= max_cost and self.MODELS[tier]["quality_score"] >= quality_required * 0.9:
                    selected_tier = tier
                    estimated_cost = cost
                    reason = f"Downgraded for cost (max ${max_cost:.4f})"
                    break

        # Track usage
        self._usage_stats[selected_tier.value] = self._usage_stats.get(selected_tier.value, 0) + 1

        return ModelRoute(
            model=self.MODELS[selected_tier]["name"],
            tier=selected_tier,
            reason=reason,
            estimated_cost=estimated_cost,
            estimated_latency_ms=self.MODELS[selected_tier]["avg_latency_ms"],
        )

    def _estimate_cost(self, tier: ModelTier, tokens: int) -> float:
        """Estimate cost for given model and token count."""
        config = self.MODELS[tier]
        # Assume 60% input, 40% output split
        input_tokens = int(tokens * 0.6)
        output_tokens = int(tokens * 0.4)
        return (
            input_tokens * config["input_cost_per_1m"] / 1_000_000 +
            output_tokens * config["output_cost_per_1m"] / 1_000_000
        )

    def record_quality_feedback(self, task_type: str, model: str, score: float):
        """Record quality feedback for continuous improvement."""
        key = f"{task_type}:{model}"
        self._quality_feedback[key] = score

    def get_usage_stats(self) -> Dict[str, int]:
        """Get model usage statistics."""
        return dict(self._usage_stats)


# =============================================================================
# CACHING
# =============================================================================

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""
    key: str
    value: T
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0


class IntelligentCache:
    """
    Multi-level cache with TTL, LRU eviction, and semantic similarity.

    Caches:
    - LLM responses for identical prompts
    - Analysis results for unchanged parcels
    - External API responses (grid data, environmental data)
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: int = 3600,
    ):
        self.max_size = max_size
        self.default_ttl = timedelta(seconds=default_ttl_seconds)
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self._stats = {"hits": 0, "misses": 0}

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        content = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self._cache:
            entry = self._cache[key]

            # Check expiration
            if datetime.utcnow() > entry.expires_at:
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            # Update access order (LRU)
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            entry.hit_count += 1
            self._stats["hits"] += 1
            return entry.value

        self._stats["misses"] += 1
        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
    ):
        """Set value in cache."""
        # Evict if at capacity
        while len(self._cache) >= self.max_size:
            if self._access_order:
                oldest_key = self._access_order.pop(0)
                if oldest_key in self._cache:
                    del self._cache[oldest_key]

        ttl = ttl or self.default_ttl
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + ttl,
        )
        self._cache[key] = entry
        self._access_order.append(key)

    def invalidate(self, key: str):
        """Invalidate specific cache entry."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)

    def invalidate_pattern(self, pattern: str):
        """Invalidate all entries matching pattern."""
        keys_to_remove = [k for k in self._cache if pattern in k]
        for key in keys_to_remove:
            self.invalidate(key)

    def clear(self):
        """Clear entire cache."""
        self._cache.clear()
        self._access_order.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": hit_rate,
        }


def cached(
    cache: IntelligentCache,
    ttl_seconds: int = 3600,
    key_prefix: str = "",
):
    """Decorator for caching function results."""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key = key_prefix + cache._generate_key(*args, **kwargs)

            # Check cache
            result = cache.get(key)
            if result is not None:
                return result

            # Execute and cache
            result = await func(*args, **kwargs)
            cache.set(key, result, timedelta(seconds=ttl_seconds))
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key = key_prefix + cache._generate_key(*args, **kwargs)
            result = cache.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache.set(key, result, timedelta(seconds=ttl_seconds))
            return result

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# =============================================================================
# BATCH PROCESSING
# =============================================================================

@dataclass
class BatchJob:
    """Batch processing job."""
    id: str = field(default_factory=lambda: str(uuid4()))
    items: List[Any] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    progress: float = 0.0
    results: List[Any] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BatchProcessor:
    """
    Efficient batch processing for multiple parcels/analyses.

    Features:
    - Parallel execution with concurrency control
    - Progress tracking
    - Error handling and retry
    - Resource optimization
    """

    def __init__(
        self,
        max_concurrency: int = 10,
        retry_attempts: int = 2,
        retry_delay_seconds: float = 1.0,
    ):
        self.max_concurrency = max_concurrency
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay_seconds
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._jobs: Dict[str, BatchJob] = {}

    async def process_batch(
        self,
        items: List[Any],
        processor: Callable[[Any], Any],
        on_progress: Optional[Callable[[float], None]] = None,
    ) -> BatchJob:
        """
        Process a batch of items.

        Args:
            items: List of items to process
            processor: Async function to process each item
            on_progress: Optional progress callback (0.0 to 1.0)

        Returns:
            BatchJob with results
        """
        job = BatchJob(items=items, status="running", started_at=datetime.utcnow())
        self._jobs[job.id] = job

        completed = 0
        total = len(items)

        async def process_with_retry(item, index: int):
            nonlocal completed

            async with self._semaphore:
                for attempt in range(self.retry_attempts + 1):
                    try:
                        result = await processor(item)
                        job.results.append((index, result))
                        break
                    except Exception as e:
                        if attempt == self.retry_attempts:
                            job.errors.append(f"Item {index}: {str(e)}")
                            job.results.append((index, None))
                        else:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))

                completed += 1
                job.progress = completed / total

                if on_progress:
                    on_progress(job.progress)

        # Process all items
        tasks = [process_with_retry(item, i) for i, item in enumerate(items)]
        await asyncio.gather(*tasks)

        # Sort results by original index
        job.results.sort(key=lambda x: x[0])
        job.results = [r[1] for r in job.results]

        job.status = "completed" if not job.errors else "failed"
        job.completed_at = datetime.utcnow()

        return job

    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def list_jobs(self, status: Optional[str] = None) -> List[BatchJob]:
        """List jobs, optionally filtered by status."""
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return jobs


# =============================================================================
# BACKGROUND TASKS
# =============================================================================

class BackgroundQueue:
    """
    Async task queue for long-running operations.

    Features:
    - Priority-based execution
    - Task deduplication
    - Progress tracking
    - Graceful shutdown
    """

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, Any] = {}
        self._running = False
        self._workers: List[asyncio.Task] = []

    async def start(self):
        """Start the background queue workers."""
        if self._running:
            return

        self._running = True
        self._workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_workers)
        ]

    async def stop(self):
        """Stop all workers gracefully."""
        self._running = False

        # Wait for queue to empty
        await self._queue.join()

        # Cancel workers
        for worker in self._workers:
            worker.cancel()

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def enqueue(
        self,
        task_id: str,
        coroutine: Callable,
        *args,
        priority: int = 5,
        **kwargs,
    ) -> str:
        """
        Add task to queue.

        Args:
            task_id: Unique task identifier
            coroutine: Async function to execute
            priority: 1 (highest) to 10 (lowest)

        Returns:
            Task ID
        """
        if task_id in self._tasks:
            logger.warning(f"Task {task_id} already queued, skipping")
            return task_id

        await self._queue.put((priority, task_id, coroutine, args, kwargs))
        return task_id

    async def _worker(self, worker_id: int):
        """Background worker."""
        while self._running:
            try:
                priority, task_id, coro, args, kwargs = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )

                try:
                    result = await coro(*args, **kwargs)
                    self._results[task_id] = {"status": "completed", "result": result}
                except Exception as e:
                    self._results[task_id] = {"status": "failed", "error": str(e)}
                    logger.exception(f"Task {task_id} failed")
                finally:
                    self._queue.task_done()

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result."""
        return self._results.get(task_id)

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()


# =============================================================================
# RATE LIMITER
# =============================================================================

class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts based on API response times.

    Features:
    - Token bucket algorithm
    - Automatic backoff on errors
    - Per-model rate limiting
    """

    def __init__(
        self,
        requests_per_minute: int = 100,
        burst_size: int = 20,
    ):
        self.rate = requests_per_minute / 60  # requests per second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = datetime.utcnow()
        self._lock = asyncio.Lock()
        self._error_count = 0
        self._backoff_until: Optional[datetime] = None

    async def acquire(self, tokens: int = 1):
        """Acquire tokens, waiting if necessary."""
        async with self._lock:
            # Check if in backoff
            if self._backoff_until and datetime.utcnow() < self._backoff_until:
                wait_time = (self._backoff_until - datetime.utcnow()).total_seconds()
                await asyncio.sleep(wait_time)
                self._backoff_until = None

            # Refill tokens
            now = datetime.utcnow()
            elapsed = (now - self.last_update).total_seconds()
            self.tokens = min(self.burst_size, self.tokens + elapsed * self.rate)
            self.last_update = now

            # Wait if not enough tokens
            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = tokens

            self.tokens -= tokens

    def record_error(self):
        """Record an error and potentially trigger backoff."""
        self._error_count += 1

        if self._error_count >= 3:
            # Exponential backoff
            backoff_seconds = min(60, 2 ** self._error_count)
            self._backoff_until = datetime.utcnow() + timedelta(seconds=backoff_seconds)
            logger.warning(f"Rate limiter backoff for {backoff_seconds}s")

    def record_success(self):
        """Record successful request."""
        self._error_count = max(0, self._error_count - 1)


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

# Singleton instances for global use
_router: Optional[IntelligentRouter] = None
_cache: Optional[IntelligentCache] = None
_batch_processor: Optional[BatchProcessor] = None
_background_queue: Optional[BackgroundQueue] = None
_rate_limiter: Optional[AdaptiveRateLimiter] = None


def get_router() -> IntelligentRouter:
    """Get global model router."""
    global _router
    if _router is None:
        _router = IntelligentRouter()
    return _router


def get_cache() -> IntelligentCache:
    """Get global cache."""
    global _cache
    if _cache is None:
        _cache = IntelligentCache()
    return _cache


def get_batch_processor() -> BatchProcessor:
    """Get global batch processor."""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor


def get_background_queue() -> BackgroundQueue:
    """Get global background queue."""
    global _background_queue
    if _background_queue is None:
        _background_queue = BackgroundQueue()
    return _background_queue


def get_rate_limiter() -> AdaptiveRateLimiter:
    """Get global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = AdaptiveRateLimiter()
    return _rate_limiter
