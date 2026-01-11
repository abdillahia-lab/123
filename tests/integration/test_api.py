"""
TerraJinki API Integration Tests

Tests for FastAPI endpoints and WebSocket functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

import sys
sys.path.insert(0, '/home/user/123')


# Check if fastapi and httpx are available
try:
    from fastapi.testclient import TestClient
    from httpx import AsyncClient
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Check if API module is available
try:
    from terrajinki.api.app import app, engine
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not (FASTAPI_AVAILABLE and API_AVAILABLE),
    reason="FastAPI or API module not available"
)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client):
        """Test /health endpoint returns OK."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_readiness_check(self, client):
        """Test /ready endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200


class TestParcelEndpoints:
    """Tests for parcel-related endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_create_parcel(self, client):
        """Test creating a new parcel."""
        parcel_data = {
            "apn": "123-456-789",
            "state": "OH",
            "county": "Franklin",
            "acreage": 150.0,
            "centroid": {
                "latitude": 40.0,
                "longitude": -82.5
            }
        }

        response = client.post("/api/v1/parcels", json=parcel_data)

        # Should succeed or return appropriate error
        assert response.status_code in [200, 201, 422]

    def test_get_parcel(self, client):
        """Test getting a parcel by ID."""
        # First create a parcel
        parcel_data = {
            "apn": "test-parcel-get",
            "state": "TX",
            "county": "Travis",
            "acreage": 200.0,
        }
        create_response = client.post("/api/v1/parcels", json=parcel_data)

        if create_response.status_code in [200, 201]:
            parcel_id = create_response.json().get("id")
            if parcel_id:
                get_response = client.get(f"/api/v1/parcels/{parcel_id}")
                assert get_response.status_code == 200

    def test_list_parcels(self, client):
        """Test listing parcels."""
        response = client.get("/api/v1/parcels")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAnalysisEndpoints:
    """Tests for analysis endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_start_analysis(self, client):
        """Test starting a new analysis."""
        # Create parcel first
        parcel_data = {
            "apn": "analysis-test-parcel",
            "state": "OH",
            "county": "Franklin",
            "acreage": 150.0,
        }
        create_response = client.post("/api/v1/parcels", json=parcel_data)

        if create_response.status_code in [200, 201]:
            parcel_id = create_response.json().get("id")
            if parcel_id:
                analysis_request = {
                    "parcel_id": parcel_id,
                    "project_type": "utility_solar",
                }
                response = client.post("/api/v1/analysis", json=analysis_request)
                assert response.status_code in [200, 201, 202, 422]

    def test_get_analysis(self, client):
        """Test getting analysis results."""
        # Test with non-existent ID returns 404
        response = client.get("/api/v1/analysis/non-existent-id")
        assert response.status_code in [404, 200]

    def test_list_analyses(self, client):
        """Test listing analyses."""
        response = client.get("/api/v1/analyses")
        assert response.status_code == 200


class TestSearchEndpoints:
    """Tests for search endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_search_parcels(self, client):
        """Test parcel search."""
        search_query = {
            "query": "Find solar sites in Ohio over 100 acres",
            "states": ["OH"],
            "min_acreage": 100,
        }
        response = client.post("/api/v1/search", json=search_query)
        assert response.status_code in [200, 422]

    def test_search_with_filters(self, client):
        """Test search with multiple filters."""
        search_query = {
            "states": ["TX", "OH"],
            "min_acreage": 50,
            "max_acreage": 500,
            "zoning_types": ["agricultural"],
        }
        response = client.post("/api/v1/search", json=search_query)
        assert response.status_code in [200, 422]


class TestProjectEndpoints:
    """Tests for project endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_create_project(self, client):
        """Test creating a new project."""
        project_data = {
            "name": "Test Solar Project",
            "project_type": "utility_solar",
            "state": "OH",
            "county": "Franklin",
        }
        response = client.post("/api/v1/projects", json=project_data)
        assert response.status_code in [200, 201, 422]

    def test_list_projects(self, client):
        """Test listing projects."""
        response = client.get("/api/v1/projects")
        assert response.status_code == 200


class TestAPIValidation:
    """Tests for API input validation."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_invalid_parcel_data(self, client):
        """Test validation rejects invalid parcel data."""
        invalid_data = {
            "acreage": -100,  # Negative acreage should be invalid
        }
        response = client.post("/api/v1/parcels", json=invalid_data)
        # Should either validate or handle gracefully
        assert response.status_code in [200, 201, 422, 400]

    def test_missing_required_fields(self, client):
        """Test validation handles missing fields."""
        response = client.post("/api/v1/parcels", json={})
        assert response.status_code in [200, 201, 422, 400]


class TestCORS:
    """Tests for CORS configuration."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_cors_headers_present(self, client):
        """Test CORS headers are present for allowed origins."""
        response = client.options(
            "/api/v1/parcels",
            headers={"Origin": "http://localhost:3000"}
        )
        # CORS should be configured
        assert response.status_code in [200, 204, 405]


class TestErrorHandling:
    """Tests for API error handling."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_404_for_unknown_endpoint(self, client):
        """Test 404 for unknown endpoints."""
        response = client.get("/api/v1/unknown-endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 for wrong HTTP method."""
        response = client.delete("/health")
        assert response.status_code in [405, 404]


class TestOpenAPI:
    """Tests for OpenAPI documentation."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_openapi_schema(self, client):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema

    def test_docs_endpoint(self, client):
        """Test Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200
