"""Rate limiting configuration for Cocktail Cache API.

This module provides global rate limiting to protect upstream API calls
(especially expensive LLM calls) from exceeding provider limits.

Privacy-first approach: No IP tracking, no user identification.
Limits are global across all users to protect API quotas.

Rate Limit Tiers:
- LLM endpoints (/api/flow): 10/minute - AI calls are expensive
- COMPUTE endpoints (/api/suggest-bottles): 30/minute - moderate resource usage
- Static data endpoints: No limit - fast local lookups
- Health endpoints: No limit - monitoring must always work
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from fastapi import HTTPException
from ratelimit import RateLimitException, sleep_and_retry
from ratelimit import limits as ratelimit_limits

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])


class RateLimits:
    """Centralized rate limit configuration.

    Tier-based limits designed for different endpoint types:
    - LLM: Very restrictive (expensive API calls)
    - COMPUTE: Moderate (CPU-intensive operations)
    - STATIC: No limit (fast, local data)
    - HEALTH: No limit (must always be available)
    """

    # LLM-powered endpoints (expensive, slow)
    LLM_CALLS = 10
    LLM_PERIOD = 60  # seconds

    # Compute-intensive endpoints (recommendation algorithms)
    COMPUTE_CALLS = 30
    COMPUTE_PERIOD = 60  # seconds


def rate_limit_llm(func: F) -> F:
    """Rate limit decorator for LLM endpoints (10 calls/minute).

    Uses sleep_and_retry to automatically wait and retry when limit is hit,
    providing a better user experience than immediate rejection.
    """

    @sleep_and_retry
    @ratelimit_limits(calls=RateLimits.LLM_CALLS, period=RateLimits.LLM_PERIOD)
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await func(*args, **kwargs)

    return cast(F, wrapper)


def rate_limit_compute(func: F) -> F:
    """Rate limit decorator for compute endpoints (30 calls/minute).

    Uses sleep_and_retry to automatically wait and retry when limit is hit.
    """

    @sleep_and_retry
    @ratelimit_limits(calls=RateLimits.COMPUTE_CALLS, period=RateLimits.COMPUTE_PERIOD)
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await func(*args, **kwargs)

    return cast(F, wrapper)


def rate_limit_llm_strict(func: F) -> F:
    """Rate limit decorator for LLM endpoints with immediate rejection.

    Raises HTTP 429 immediately when limit is exceeded instead of waiting.
    Use this when you want to fail fast rather than queue requests.
    """

    @ratelimit_limits(calls=RateLimits.LLM_CALLS, period=RateLimits.LLM_PERIOD)
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except RateLimitException as e:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
            ) from e

    return cast(F, wrapper)


def rate_limit_compute_strict(func: F) -> F:
    """Rate limit decorator for compute endpoints with immediate rejection.

    Raises HTTP 429 immediately when limit is exceeded.
    """

    @ratelimit_limits(calls=RateLimits.COMPUTE_CALLS, period=RateLimits.COMPUTE_PERIOD)
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except RateLimitException as e:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
            ) from e

    return cast(F, wrapper)
