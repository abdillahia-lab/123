"""
TerraJinki Configuration Unit Tests

Tests for configuration loading, validation, and environment handling.
"""

import pytest
import os
from unittest.mock import patch

import sys
sys.path.insert(0, '/home/user/123')

from terrajinki.core.config import (
    TerraJinkiConfig, LLMConfig, DatabaseConfig, AgentConfig,
    ScoringConfig, APIConfig, MLConfig, DataSourceConfig,
    Environment, get_config, set_config
)


class TestLLMConfig:
    """Tests for LLMConfig class."""

    def test_default_values(self):
        """Test LLMConfig default values."""
        config = LLMConfig()
        assert config.anthropic_model_orchestrator == "claude-opus-4-5-20251101"
        assert config.anthropic_model_analysis == "claude-sonnet-4-20250514"
        assert config.max_requests_per_minute == 100

    def test_from_env(self):
        """Test loading from environment variables."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key-123"}):
            config = LLMConfig.from_env()
            assert config.anthropic_api_key == "test-key-123"

    def test_cost_limits(self):
        """Test cost limit defaults."""
        config = LLMConfig()
        assert config.max_cost_per_analysis == 5.0
        assert config.max_cost_per_day == 100.0


class TestDatabaseConfig:
    """Tests for DatabaseConfig class."""

    def test_default_values(self):
        """Test DatabaseConfig defaults."""
        config = DatabaseConfig()
        assert config.postgres_host == "localhost"
        assert config.postgres_port == 5432
        assert config.postgres_db == "terrajinki"

    def test_postgres_url(self):
        """Test PostgreSQL URL generation."""
        config = DatabaseConfig(
            postgres_host="db.example.com",
            postgres_port=5433,
            postgres_db="mydb",
            postgres_user="myuser",
            postgres_password="secret"
        )
        url = config.postgres_url
        assert "db.example.com" in url
        assert "5433" in url
        assert "mydb" in url
        assert "myuser" in url

    def test_redis_url_without_password(self):
        """Test Redis URL without password."""
        config = DatabaseConfig(redis_host="redis.local", redis_port=6380)
        url = config.redis_url
        assert url == "redis://redis.local:6380/0"

    def test_redis_url_with_password(self):
        """Test Redis URL with password."""
        config = DatabaseConfig(redis_password="secret123")
        url = config.redis_url
        assert ":secret123@" in url


class TestAgentConfig:
    """Tests for AgentConfig class."""

    def test_default_timeouts(self):
        """Test default timeout values."""
        config = AgentConfig()
        assert config.agent_timeout_seconds == 60.0
        assert config.swarm_timeout_seconds == 120.0
        assert config.orchestrator_timeout_seconds == 300.0

    def test_parallelism_limits(self):
        """Test parallelism defaults."""
        config = AgentConfig()
        assert config.max_parallel_agents == 10
        assert config.max_parallel_swarms == 4

    def test_approval_thresholds(self):
        """Test approval threshold values."""
        config = AgentConfig()
        assert config.fatal_flaw_score_threshold == 30.0
        assert config.high_value_score_threshold == 90.0
        assert config.fatal_flaw_score_threshold < config.high_value_score_threshold


class TestScoringConfig:
    """Tests for ScoringConfig class."""

    def test_default_weights(self):
        """Test default weight values."""
        config = ScoringConfig()
        assert config.permitting_weight == 0.30
        assert config.grid_weight == 0.30
        assert config.environmental_weight == 0.20
        assert config.land_weight == 0.10
        assert config.financial_weight == 0.10

    def test_validate_weights_correct(self):
        """Test weight validation passes with correct weights."""
        config = ScoringConfig()
        assert config.validate_weights() is True

    def test_validate_weights_incorrect(self):
        """Test weight validation fails with incorrect weights."""
        config = ScoringConfig(permitting_weight=0.5)  # Sum now > 1.0
        assert config.validate_weights() is False

    def test_thresholds(self):
        """Test score threshold values."""
        config = ScoringConfig()
        assert config.excellent_threshold > config.good_threshold
        assert config.good_threshold > config.moderate_threshold
        assert config.moderate_threshold > config.challenging_threshold
        assert config.challenging_threshold > config.poor_threshold

    def test_fatal_flaw_conditions(self):
        """Test fatal flaw condition list."""
        config = ScoringConfig()
        assert "solar_prohibited" in config.fatal_flaw_conditions
        assert "no_grid_access" in config.fatal_flaw_conditions


class TestAPIConfig:
    """Tests for APIConfig class."""

    def test_default_values(self):
        """Test APIConfig defaults."""
        config = APIConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.debug is False

    def test_cors_origins(self):
        """Test CORS origins default."""
        config = APIConfig()
        assert "http://localhost:3000" in config.cors_origins

    def test_from_env(self):
        """Test loading from environment."""
        with patch.dict(os.environ, {
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
            "API_DEBUG": "true"
        }):
            config = APIConfig.from_env()
            assert config.host == "127.0.0.1"
            assert config.port == 9000
            assert config.debug is True


class TestTerraJinkiConfig:
    """Tests for TerraJinkiConfig master config."""

    def test_default_environment(self):
        """Test default environment is development."""
        config = TerraJinkiConfig()
        assert config.environment == Environment.DEVELOPMENT

    def test_component_configs_present(self):
        """Test all component configs are present."""
        config = TerraJinkiConfig()
        assert config.llm is not None
        assert config.database is not None
        assert config.agents is not None
        assert config.scoring is not None
        assert config.api is not None
        assert config.ml is not None

    def test_feature_flags(self):
        """Test feature flag defaults."""
        config = TerraJinkiConfig()
        assert config.enable_satellite_analysis is True
        assert config.enable_gnn_grid_analysis is True
        assert config.enable_rag_ordinances is True
        assert config.enable_human_in_loop is True

    def test_validate_development(self):
        """Test validation passes in development."""
        config = TerraJinkiConfig(environment=Environment.DEVELOPMENT)
        issues = config.validate()
        assert len(issues) == 0

    def test_validate_production_missing_key(self):
        """Test validation fails in production without API key."""
        config = TerraJinkiConfig(
            environment=Environment.PRODUCTION,
            llm=LLMConfig(anthropic_api_key=""),
        )
        issues = config.validate()
        assert any("ANTHROPIC_API_KEY" in issue for issue in issues)

    def test_validate_production_with_key(self):
        """Test validation passes in production with API key."""
        config = TerraJinkiConfig(
            environment=Environment.PRODUCTION,
            llm=LLMConfig(anthropic_api_key="prod-key-123"),
            api=APIConfig(jwt_secret="secret-123"),
        )
        issues = config.validate()
        assert len(issues) == 0

    def test_validate_scoring_weights(self):
        """Test validation catches bad scoring weights."""
        config = TerraJinkiConfig(
            scoring=ScoringConfig(permitting_weight=0.5)  # Invalid
        )
        issues = config.validate()
        assert any("weights" in issue.lower() for issue in issues)

    def test_is_production(self):
        """Test is_production helper."""
        dev_config = TerraJinkiConfig(environment=Environment.DEVELOPMENT)
        prod_config = TerraJinkiConfig(environment=Environment.PRODUCTION)

        assert dev_config.is_production() is False
        assert prod_config.is_production() is True

    def test_get_llm_model(self):
        """Test LLM model selection by tier."""
        config = TerraJinkiConfig()

        assert "opus" in config.get_llm_model("orchestrator")
        assert "sonnet" in config.get_llm_model("analysis")
        assert "haiku" in config.get_llm_model("fast")

    def test_from_env(self):
        """Test loading full config from environment."""
        with patch.dict(os.environ, {
            "TERRAJINKI_ENV": "staging",
            "ANTHROPIC_API_KEY": "test-key",
            "LOG_LEVEL": "DEBUG",
        }):
            config = TerraJinkiConfig.from_env()
            assert config.environment == Environment.STAGING
            assert config.llm.anthropic_api_key == "test-key"
            assert config.log_level == "DEBUG"


class TestGlobalConfig:
    """Tests for global config management."""

    def test_set_and_get_config(self, test_config):
        """Test setting and getting global config."""
        set_config(test_config)
        retrieved = get_config()
        assert retrieved is test_config

    def test_get_config_creates_default(self):
        """Test get_config creates default if none set."""
        # Reset global config
        import terrajinki.core.config as cfg
        cfg._config = None

        config = get_config()
        assert config is not None
        assert config.app_name == "TerraJinki"


class TestEnvironmentEnum:
    """Tests for Environment enum."""

    def test_values(self):
        """Test environment values."""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"

    def test_string_comparison(self):
        """Test string comparison works."""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.PRODUCTION == "production"
