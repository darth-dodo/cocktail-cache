"""Tests for rate limiting functionality.

Tests verify that rate limiting configuration is correctly set up with:
- Correct rate limit constants for different tiers (LLM, COMPUTE)
- Decorator functions are properly configured
- Privacy-first approach (no IP tracking, global limits)

Note: The ratelimit library uses sleep_and_retry for the default decorators,
which will wait and retry rather than returning 429 immediately. The strict
variants raise HTTP 429 when limits are exceeded.
"""

import pytest

from src.app.rate_limit import (
    RateLimits,
    rate_limit_compute,
    rate_limit_compute_strict,
    rate_limit_llm,
    rate_limit_llm_strict,
)

# =============================================================================
# Rate Limit Configuration Tests
# =============================================================================


class TestRateLimitConfiguration:
    """Tests for rate limit configuration values."""

    def test_llm_calls_constant(self):
        """LLM tier allows 10 calls per period."""
        assert RateLimits.LLM_CALLS == 10

    def test_llm_period_constant(self):
        """LLM tier period is 60 seconds."""
        assert RateLimits.LLM_PERIOD == 60

    def test_compute_calls_constant(self):
        """COMPUTE tier allows 30 calls per period."""
        assert RateLimits.COMPUTE_CALLS == 30

    def test_compute_period_constant(self):
        """COMPUTE tier period is 60 seconds."""
        assert RateLimits.COMPUTE_PERIOD == 60

    def test_llm_more_restrictive_than_compute(self):
        """LLM tier is more restrictive than COMPUTE tier."""
        assert RateLimits.LLM_CALLS < RateLimits.COMPUTE_CALLS

    def test_both_tiers_have_same_period(self):
        """Both tiers use the same time period for consistency."""
        assert RateLimits.LLM_PERIOD == RateLimits.COMPUTE_PERIOD


# =============================================================================
# Decorator Existence Tests
# =============================================================================


class TestDecoratorExistence:
    """Tests verifying rate limit decorators exist and are callable."""

    def test_rate_limit_llm_is_callable(self):
        """rate_limit_llm decorator is callable."""
        assert callable(rate_limit_llm)

    def test_rate_limit_compute_is_callable(self):
        """rate_limit_compute decorator is callable."""
        assert callable(rate_limit_compute)

    def test_rate_limit_llm_strict_is_callable(self):
        """rate_limit_llm_strict decorator is callable."""
        assert callable(rate_limit_llm_strict)

    def test_rate_limit_compute_strict_is_callable(self):
        """rate_limit_compute_strict decorator is callable."""
        assert callable(rate_limit_compute_strict)


# =============================================================================
# Decorator Behavior Tests
# =============================================================================


class TestDecoratorBehavior:
    """Tests verifying decorator behavior preserves function metadata."""

    def test_rate_limit_llm_preserves_function_name(self):
        """rate_limit_llm decorator preserves wrapped function name."""

        @rate_limit_llm
        async def my_llm_function():
            return "result"

        assert my_llm_function.__name__ == "my_llm_function"

    def test_rate_limit_compute_preserves_function_name(self):
        """rate_limit_compute decorator preserves wrapped function name."""

        @rate_limit_compute
        async def my_compute_function():
            return "result"

        assert my_compute_function.__name__ == "my_compute_function"

    def test_rate_limit_llm_strict_preserves_function_name(self):
        """rate_limit_llm_strict decorator preserves wrapped function name."""

        @rate_limit_llm_strict
        async def my_strict_llm_function():
            return "result"

        assert my_strict_llm_function.__name__ == "my_strict_llm_function"

    def test_rate_limit_compute_strict_preserves_function_name(self):
        """rate_limit_compute_strict decorator preserves wrapped function name."""

        @rate_limit_compute_strict
        async def my_strict_compute_function():
            return "result"

        assert my_strict_compute_function.__name__ == "my_strict_compute_function"


# =============================================================================
# Privacy-First Configuration Tests
# =============================================================================


class TestPrivacyFirstConfiguration:
    """Tests verifying privacy-first approach in rate limiting."""

    def test_no_ip_tracking_in_configuration(self):
        """RateLimits class has no IP-related configuration."""
        # Verify RateLimits doesn't have any IP-related attributes
        rate_limit_attrs = [
            attr for attr in dir(RateLimits) if not attr.startswith("_")
        ]
        ip_related = [attr for attr in rate_limit_attrs if "ip" in attr.lower()]
        assert len(ip_related) == 0, "Rate limiting should not track IP addresses"

    def test_no_user_tracking_in_configuration(self):
        """RateLimits class has no user-related configuration."""
        # Verify RateLimits doesn't have any user-related attributes
        rate_limit_attrs = [
            attr for attr in dir(RateLimits) if not attr.startswith("_")
        ]
        user_related = [
            attr
            for attr in rate_limit_attrs
            if "user" in attr.lower() or "client" in attr.lower()
        ]
        assert len(user_related) == 0, "Rate limiting should not track users"

    def test_rate_limits_are_global_constants(self):
        """Rate limits are defined as class constants (global, not per-user)."""
        # Verify the configuration is simple class attributes
        assert isinstance(RateLimits.LLM_CALLS, int)
        assert isinstance(RateLimits.LLM_PERIOD, int)
        assert isinstance(RateLimits.COMPUTE_CALLS, int)
        assert isinstance(RateLimits.COMPUTE_PERIOD, int)


# =============================================================================
# API Endpoint Tests (No Rate Limiting on Static Endpoints)
# =============================================================================


class TestStaticEndpointsNoRateLimit:
    """Tests verifying static endpoints work without rate limiting."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from fastapi.testclient import TestClient

        from src.app.main import app

        return TestClient(app)

    def test_drinks_endpoint_works(self, client):
        """GET /api/drinks works (no rate limiting on static endpoints)."""
        response = client.get("/api/drinks")
        assert response.status_code == 200

    def test_drinks_detail_endpoint_works(self, client):
        """GET /api/drinks/{id} works (no rate limiting on static endpoints)."""
        response = client.get("/api/drinks/old-fashioned")
        assert response.status_code == 200

    def test_ingredients_endpoint_works(self, client):
        """GET /api/ingredients works (no rate limiting on static endpoints)."""
        response = client.get("/api/ingredients")
        assert response.status_code == 200

    def test_multiple_static_requests_succeed(self, client):
        """Multiple requests to static endpoints all succeed."""
        # Make many requests - should all succeed since static endpoints
        # have no rate limiting
        for i in range(50):
            response = client.get("/api/drinks")
            assert response.status_code == 200, f"Request {i + 1} should succeed"


# =============================================================================
# Health Endpoint Tests
# =============================================================================


class TestHealthEndpoint:
    """Tests verifying health endpoint always works."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from fastapi.testclient import TestClient

        from src.app.main import app

        return TestClient(app)

    def test_health_endpoint_returns_200(self, client):
        """Health endpoint returns expected healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_endpoint_always_succeeds(self, client):
        """Health endpoint succeeds even after many requests."""
        # Make many requests to health endpoint
        for i in range(100):
            response = client.get("/health")
            assert response.status_code == 200, f"Health request {i + 1} should succeed"


# =============================================================================
# COMPUTE Endpoint Tests
# =============================================================================


class TestComputeEndpoint:
    """Tests for COMPUTE tier endpoint (/api/suggest-bottles)."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from fastapi.testclient import TestClient

        from src.app.main import app

        return TestClient(app)

    def test_suggest_bottles_endpoint_works(self, client):
        """POST /api/suggest-bottles works within limits."""
        response = client.post("/api/suggest-bottles", json={"cabinet": [], "limit": 3})
        assert response.status_code == 200

    def test_suggest_bottles_returns_valid_response(self, client):
        """POST /api/suggest-bottles returns expected response format."""
        response = client.post("/api/suggest-bottles", json={"cabinet": [], "limit": 3})
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
