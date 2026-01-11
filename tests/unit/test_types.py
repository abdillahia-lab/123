"""
TerraJinki Core Types Unit Tests

Tests for geographic types, parcel data, and site scoring.
"""

import pytest
import math
from datetime import datetime

import sys
sys.path.insert(0, '/home/user/123')

from terrajinki.core.types import (
    GeoPoint, GeoPolygon, BoundingBox, Parcel,
    ZoningType, SolarPermission, ProjectType, ProjectStage,
    SiteScore, SiteAnalysis, AgentResult, SwarmResult, AgentStatus,
    EnvironmentalRisk, GridViability, ApprovalLevel,
)


class TestGeoPoint:
    """Tests for GeoPoint class."""

    def test_creation(self, sample_geo_point):
        """Test GeoPoint creation."""
        assert sample_geo_point.latitude == 40.0
        assert sample_geo_point.longitude == -82.5
        assert sample_geo_point.elevation_m == 300.0

    def test_distance_to_same_point(self):
        """Distance to same point should be zero."""
        p1 = GeoPoint(latitude=40.0, longitude=-82.5)
        p2 = GeoPoint(latitude=40.0, longitude=-82.5)
        assert p1.distance_to(p2) == 0.0

    def test_distance_calculation(self):
        """Test Haversine distance calculation."""
        # Columbus, OH to Cleveland, OH (~130 miles)
        columbus = GeoPoint(latitude=39.9612, longitude=-82.9988)
        cleveland = GeoPoint(latitude=41.4993, longitude=-81.6944)
        distance = columbus.distance_to(cleveland)
        assert 120 < distance < 140  # Approximate check

    def test_distance_symmetry(self):
        """Distance should be symmetric."""
        p1 = GeoPoint(latitude=40.0, longitude=-82.5)
        p2 = GeoPoint(latitude=41.0, longitude=-83.5)
        assert abs(p1.distance_to(p2) - p2.distance_to(p1)) < 0.001

    def test_to_geojson(self, sample_geo_point):
        """Test GeoJSON conversion."""
        geojson = sample_geo_point.to_geojson()
        assert geojson["type"] == "Point"
        assert geojson["coordinates"] == [-82.5, 40.0]


class TestGeoPolygon:
    """Tests for GeoPolygon class."""

    def test_centroid_calculation(self, sample_geo_polygon):
        """Test polygon centroid calculation."""
        centroid = sample_geo_polygon.centroid
        assert 40.0 < centroid.latitude < 40.01
        assert -82.5 < centroid.longitude < -82.49

    def test_empty_polygon_centroid_raises(self):
        """Empty polygon should raise error on centroid."""
        poly = GeoPolygon(vertices=[])
        with pytest.raises(ValueError):
            _ = poly.centroid

    def test_area_calculation(self, sample_geo_polygon):
        """Test area calculation returns positive value."""
        area = sample_geo_polygon.area_acres
        assert area > 0

    def test_small_polygon_area(self):
        """Very small polygon should have near-zero area."""
        tiny = GeoPolygon(vertices=[
            GeoPoint(latitude=40.0, longitude=-82.5),
            GeoPoint(latitude=40.00001, longitude=-82.5),
            GeoPoint(latitude=40.0, longitude=-82.49999),
        ])
        assert tiny.area_acres < 1.0

    def test_to_geojson(self, sample_geo_polygon):
        """Test GeoJSON conversion with closed ring."""
        geojson = sample_geo_polygon.to_geojson()
        assert geojson["type"] == "Polygon"
        coords = geojson["coordinates"][0]
        # Ring should be closed
        assert coords[0] == coords[-1]


class TestBoundingBox:
    """Tests for BoundingBox class."""

    def test_contains_point_inside(self):
        """Point inside bounding box should return True."""
        bbox = BoundingBox(min_lat=39.0, min_lon=-83.0, max_lat=41.0, max_lon=-81.0)
        point = GeoPoint(latitude=40.0, longitude=-82.0)
        assert bbox.contains(point) is True

    def test_contains_point_outside(self):
        """Point outside bounding box should return False."""
        bbox = BoundingBox(min_lat=39.0, min_lon=-83.0, max_lat=41.0, max_lon=-81.0)
        point = GeoPoint(latitude=35.0, longitude=-82.0)
        assert bbox.contains(point) is False

    def test_contains_point_on_edge(self):
        """Point on edge should be contained."""
        bbox = BoundingBox(min_lat=39.0, min_lon=-83.0, max_lat=41.0, max_lon=-81.0)
        point = GeoPoint(latitude=39.0, longitude=-82.0)
        assert bbox.contains(point) is True


class TestParcel:
    """Tests for Parcel class."""

    def test_creation_with_defaults(self):
        """Test Parcel creation with default values."""
        parcel = Parcel()
        assert parcel.id is not None
        assert parcel.acreage == 0.0
        assert parcel.zoning_type == ZoningType.AGRICULTURAL

    def test_creation_with_values(self, sample_parcel):
        """Test Parcel with provided values."""
        assert sample_parcel.id == "test-parcel-001"
        assert sample_parcel.state == "OH"
        assert sample_parcel.county == "Franklin"
        assert sample_parcel.acreage == 150.0
        assert sample_parcel.zoning_type == ZoningType.AGRICULTURAL

    def test_to_dict(self, sample_parcel):
        """Test Parcel dictionary conversion."""
        d = sample_parcel.to_dict()
        assert d["id"] == "test-parcel-001"
        assert d["apn"] == "123-456-789"
        assert d["state"] == "OH"
        assert d["acreage"] == 150.0
        assert d["zoning_type"] == "agricultural"

    def test_centroid_geojson(self, sample_parcel):
        """Test parcel centroid in dict."""
        d = sample_parcel.to_dict()
        assert d["centroid"]["type"] == "Point"


class TestSiteScore:
    """Tests for SiteScore class."""

    def test_calculate_overall(self):
        """Test overall score calculation."""
        score = SiteScore(
            permitting_score=80.0,
            grid_score=70.0,
            environmental_score=90.0,
            land_score=60.0,
            financial_score=50.0,
        )
        result = score.calculate_overall()

        # Expected: 80*0.3 + 70*0.3 + 90*0.2 + 60*0.1 + 50*0.1 = 24 + 21 + 18 + 6 + 5 = 74
        assert abs(result - 74.0) < 0.1

    def test_viability_excellent(self):
        """Test excellent viability classification."""
        score = SiteScore(
            permitting_score=95.0,
            grid_score=92.0,
            environmental_score=95.0,
            land_score=88.0,
            financial_score=85.0,
        )
        score.calculate_overall()
        assert score.viability == "excellent"
        assert score.star_rating == 5

    def test_viability_good(self):
        """Test good viability classification."""
        score = SiteScore(
            permitting_score=80.0,
            grid_score=78.0,
            environmental_score=80.0,
            land_score=70.0,
            financial_score=65.0,
        )
        score.calculate_overall()
        assert score.viability == "good"
        assert score.star_rating == 4

    def test_viability_moderate(self):
        """Test moderate viability classification."""
        score = SiteScore(
            permitting_score=65.0,
            grid_score=62.0,
            environmental_score=68.0,
            land_score=55.0,
            financial_score=50.0,
        )
        score.calculate_overall()
        assert score.viability == "moderate"
        assert score.star_rating == 3

    def test_viability_challenging(self):
        """Test challenging viability classification."""
        score = SiteScore(
            permitting_score=45.0,
            grid_score=42.0,
            environmental_score=48.0,
            land_score=35.0,
            financial_score=30.0,
        )
        score.calculate_overall()
        assert score.viability == "challenging"
        assert score.star_rating == 2

    def test_viability_poor(self):
        """Test poor viability classification."""
        score = SiteScore(
            permitting_score=25.0,
            grid_score=22.0,
            environmental_score=28.0,
            land_score=15.0,
            financial_score=10.0,
        )
        score.calculate_overall()
        assert score.viability == "poor"
        assert score.star_rating == 1

    def test_viability_fatal(self):
        """Test fatal viability classification."""
        score = SiteScore(
            permitting_score=10.0,
            grid_score=5.0,
            environmental_score=15.0,
            land_score=5.0,
            financial_score=0.0,
        )
        score.calculate_overall()
        assert score.viability == "fatal"
        assert score.star_rating == 0

    def test_custom_weights(self):
        """Test custom weight application."""
        score = SiteScore(
            permitting_score=100.0,
            grid_score=0.0,
            environmental_score=0.0,
            land_score=0.0,
            financial_score=0.0,
            permitting_weight=1.0,
            grid_weight=0.0,
            environmental_weight=0.0,
            land_weight=0.0,
            financial_weight=0.0,
        )
        result = score.calculate_overall()
        assert result == 100.0


class TestAgentResult:
    """Tests for AgentResult class."""

    def test_creation_defaults(self):
        """Test AgentResult with defaults."""
        result = AgentResult()
        assert result.status == AgentStatus.COMPLETED
        assert result.success is True
        assert result.score == 0.0

    def test_creation_with_values(self, sample_agent_result):
        """Test AgentResult with values."""
        assert sample_agent_result.agent_id == "test-agent-001"
        assert sample_agent_result.score == 75.0
        assert sample_agent_result.confidence == 0.85

    def test_error_state(self):
        """Test AgentResult in error state."""
        result = AgentResult(
            status=AgentStatus.FAILED,
            success=False,
            error_message="API timeout",
        )
        assert result.success is False
        assert result.status == AgentStatus.FAILED


class TestSwarmResult:
    """Tests for SwarmResult class."""

    def test_creation(self, sample_swarm_result):
        """Test SwarmResult creation."""
        assert sample_swarm_result.swarm_type == "permitting"
        assert len(sample_swarm_result.agent_results) == 1
        assert sample_swarm_result.overall_score == 75.0

    def test_empty_results(self):
        """Test SwarmResult with no agent results."""
        result = SwarmResult(swarm_id="empty", swarm_type="test")
        assert len(result.agent_results) == 0


class TestEnumerations:
    """Tests for enumeration types."""

    def test_project_type_values(self):
        """Test ProjectType enum values."""
        assert ProjectType.UTILITY_SOLAR.value == "utility_solar"
        assert ProjectType.WIND_ONSHORE.value == "wind_onshore"
        assert ProjectType.BATTERY_STORAGE.value == "battery_storage"

    def test_project_stage_values(self):
        """Test ProjectStage enum values."""
        assert ProjectStage.PROSPECTING.value == "prospecting"
        assert ProjectStage.PERMITTING.value == "permitting"
        assert ProjectStage.CONSTRUCTION.value == "construction"

    def test_zoning_type_values(self):
        """Test ZoningType enum values."""
        assert ZoningType.AGRICULTURAL.value == "agricultural"
        assert ZoningType.INDUSTRIAL.value == "industrial"

    def test_solar_permission_values(self):
        """Test SolarPermission enum values."""
        assert SolarPermission.BY_RIGHT.value == "by_right"
        assert SolarPermission.PROHIBITED.value == "prohibited"

    def test_environmental_risk_values(self):
        """Test EnvironmentalRisk enum values."""
        assert EnvironmentalRisk.NONE.value == "none"
        assert EnvironmentalRisk.FATAL.value == "fatal"

    def test_grid_viability_values(self):
        """Test GridViability enum values."""
        assert GridViability.EXCELLENT.value == "excellent"
        assert GridViability.FATAL.value == "fatal"

    def test_approval_level_values(self):
        """Test ApprovalLevel enum values."""
        assert ApprovalLevel.AUTONOMOUS.value == "autonomous"
        assert ApprovalLevel.APPROVE.value == "approve"


class TestSiteAnalysis:
    """Tests for SiteAnalysis class."""

    def test_creation(self, sample_site_analysis):
        """Test SiteAnalysis creation."""
        assert sample_site_analysis.parcel_id == "test-parcel-001"
        assert sample_site_analysis.project_type == ProjectType.UTILITY_SOLAR

    def test_score_assignment(self, sample_site_analysis, sample_site_score):
        """Test score is properly assigned."""
        assert sample_site_analysis.score is not None
        assert sample_site_analysis.score.overall_score > 0

    def test_recommendations(self, sample_site_analysis):
        """Test recommendations are present."""
        assert len(sample_site_analysis.recommended_next_steps) > 0
        assert sample_site_analysis.proceed_recommendation == "proceed_with_caution"
