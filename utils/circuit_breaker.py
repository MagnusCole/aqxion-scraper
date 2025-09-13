"""
Circuit Breaker Pattern for Aqxion Scraper
Provides resilient API call handling with automatic failure recovery
"""

import asyncio
import time
from enum import Enum
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

# Import constants from config
from config.config_v2 import MIN_TITLE_LENGTH

log = logging.getLogger("circuit_breaker")

class CircuitBreakerState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"     # Normal operation
    OPEN = "open"         # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerMetrics:
    """Métricas del circuit breaker"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: int = 0

@dataclass
class CircuitBreakerConfig:
    """Configuración del circuit breaker"""
    failure_threshold: int = 5  # Failures to trigger open state
    recovery_timeout: int = 60  # Seconds to wait before trying recovery
    success_threshold: int = 3  # Successes needed to close circuit
    timeout: float = 30.0       # Request timeout in seconds
    name: str = "default"

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class AsyncCircuitBreaker:
    """Circuit Breaker implementation for async operations"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self._lock = asyncio.Lock()
        self._last_state_change = datetime.now()

        log.info(f"🔌 Circuit Breaker '{config.name}' initialized - Failure threshold: {config.failure_threshold}")

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            self.metrics.total_requests += 1

            # Check if circuit should be opened
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    await self._transition_to_half_open()
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.config.name}' is OPEN. "
                        f"Last failure: {self.metrics.last_failure_time}"
                    )

            # Execute the function
            try:
                if self.state == CircuitBreakerState.HALF_OPEN:
                    # Use timeout for half-open state
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.config.timeout
                    )
                else:
                    result = await func(*args, **kwargs)

                await self._on_success()
                return result

            except asyncio.TimeoutError:
                await self._on_failure("timeout")
                raise
            except Exception as e:
                await self._on_failure(str(e))
                raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.metrics.last_failure_time is None:
            return True

        time_since_failure = datetime.now() - self.metrics.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout

    async def _transition_to_half_open(self):
        """Transition to half-open state for testing"""
        self.state = CircuitBreakerState.HALF_OPEN
        self.metrics.state_changes += 1
        self._last_state_change = datetime.now()
        log.info(f"🔄 Circuit Breaker '{self.config.name}' -> HALF_OPEN (testing recovery)")

    async def _on_success(self):
        """Handle successful request"""
        self.metrics.successful_requests += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_success_time = datetime.now()

        if self.state == CircuitBreakerState.HALF_OPEN:
            # Check if we have enough successes to close
            if self.metrics.successful_requests >= self.config.success_threshold:
                await self._close_circuit()
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset consecutive failures on success
            self.metrics.consecutive_failures = 0

    async def _on_failure(self, reason: str):
        """Handle failed request"""
        self.metrics.failed_requests += 1
        self.metrics.consecutive_failures += 1
        self.metrics.last_failure_time = datetime.now()

        if self.state == CircuitBreakerState.HALF_OPEN:
            # Any failure in half-open state sends us back to open
            await self._open_circuit()
        elif (self.state == CircuitBreakerState.CLOSED and
              self.metrics.consecutive_failures >= self.config.failure_threshold):
            await self._open_circuit()

        log.warning(f"❌ Circuit Breaker '{self.config.name}' failure #{self.metrics.consecutive_failures}: {reason}")

    async def _open_circuit(self):
        """Open the circuit breaker"""
        self.state = CircuitBreakerState.OPEN
        self.metrics.state_changes += 1
        self._last_state_change = datetime.now()
        log.error(f"🚫 Circuit Breaker '{self.config.name}' -> OPEN (too many failures)")

    async def _close_circuit(self):
        """Close the circuit breaker"""
        self.state = CircuitBreakerState.CLOSED
        self.metrics.state_changes += 1
        self._last_state_change = datetime.now()
        log.info(f"✅ Circuit Breaker '{self.config.name}' -> CLOSED (recovery successful)")

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        success_rate = (self.metrics.successful_requests / self.metrics.total_requests * 100
                       if self.metrics.total_requests > 0 else 0)

        return {
            "name": self.config.name,
            "state": self.state.value,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "consecutive_failures": self.metrics.consecutive_failures,
            "success_rate": round(success_rate, 2),
            "last_failure": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
            "last_success": self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
            "state_changes": self.metrics.state_changes,
            "time_in_current_state": (datetime.now() - self._last_state_change).total_seconds()
        }

    async def reset(self):
        """Manually reset the circuit breaker"""
        async with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self.metrics = CircuitBreakerMetrics()
            self._last_state_change = datetime.now()
            log.info(f"🔄 Circuit Breaker '{self.config.name}' manually reset")

# Global circuit breaker instances
openai_circuit_breaker = AsyncCircuitBreaker(
    CircuitBreakerConfig(
        name="openai_api",
        failure_threshold=3,  # Open after 3 failures
        recovery_timeout=MIN_TITLE_LENGTH,  # Wait MIN_TITLE_LENGTH seconds before retry
        success_threshold=2,  # Need 2 successes to close
        timeout=25.0  # 25 second timeout for API calls
    )
)

# Fallback circuit breaker for when OpenAI is down
fallback_circuit_breaker = AsyncCircuitBreaker(
    CircuitBreakerConfig(
        name="fallback_processing",
        failure_threshold=5,
        recovery_timeout=60,
        success_threshold=1,
        timeout=10.0
    )
)

async def with_circuit_breaker(circuit_breaker: AsyncCircuitBreaker, func: Callable, *args, **kwargs) -> Any:
    """Helper function to use circuit breaker with any async function"""
    return await circuit_breaker.call(func, *args, **kwargs)

def get_circuit_breaker_status() -> Dict[str, Any]:
    """Get status of all circuit breakers"""
    async def _get_status():
        openai_status = await openai_circuit_breaker.get_metrics()
        fallback_status = await fallback_circuit_breaker.get_metrics()
        return {
            "openai": openai_status,
            "fallback": fallback_status,
            "overall_health": "healthy" if openai_status["state"] == "closed" else "degraded"
        }

    # Run in event loop if available, otherwise return sync version
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create task for later execution
            return loop.create_task(_get_status())
        else:
            return loop.run_until_complete(_get_status())
    except RuntimeError:
        # No event loop, return basic info
        return {
            "openai": {"state": openai_circuit_breaker.state.value},
            "fallback": {"state": fallback_circuit_breaker.state.value},
            "overall_health": "unknown"
        }