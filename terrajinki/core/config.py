"""
TerraJinki Configuration

Centralized configuration management with environment variable support
and validation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import os
from enum import Enum


class Environment(str, Enum):
    """Deployment environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    # Primary provider (Claude)
    anthropic_api_key: str = ""
    anthropic_model_orchestrator: str = "claude-opus-4-5-20251101"
    anthropic_model_analysis: str = "claude-sonnet-4-20250514"
    anthropic_model_fast: str = "claude-3-5-haiku-20241022"

    # Fallback provider (OpenAI)
    openai_api_key: str = ""
    openai_model_primary: str = "gpt-4o"
    openai_model_fast: str = "gpt-4o-mini"

    # Rate limiting
    max_tokens_per_minute: int = 100000
    max_requests_per_minute: int = 100
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0

    # Cost tracking
    max_cost_per_analysis: float = 5.0  # USD
    max_cost_per_day: float = 100.0

    @classmethod
    def from_env(cls) -> LLMConfig:
        """Load from environment variables."""
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        )


@dataclass
class DatabaseConfig:
    """Database configuration."""
    # PostgreSQL + PostGIS
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "terrajinki"
    postgres_user: str = "terrajinki"
    postgres_password: str = ""

    # Connection pool
    pool_size: int = 10
    max_overflow: int = 20

    # Vector database (Qdrant)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""

    # Redis cache
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Load from environment variables."""
        return cls(
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_db=os.getenv("POSTGRES_DB", "terrajinki"),
            postgres_user=os.getenv("POSTGRES_USER", "terrajinki"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
            qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
            qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
        )


@dataclass
class DataSourceConfig:
    """External data source API configuration."""
    # Parcel data
    regrid_api_key: str = ""
    regrid_base_url: str = "https://api.regrid.com/v1"

    # Grid data
    eia_api_key: str = ""
    eia_base_url: str = "https://api.eia.gov/v2"

    # Environmental
    nwi_base_url: str = "https://www.fws.gov/wetlands/data/web-map-services.html"
    fema_base_url: str = "https://hazards.fema.gov/gis/nfhl/rest/services"
    usfws_ipac_url: str = "https://ipac.ecosphere.fws.gov"

    # Solar resource
    nsrdb_api_key: str = ""
    nsrdb_base_url: str = "https://developer.nrel.gov/api/nsrdb"
    pvgis_base_url: str = "https://re.jrc.ec.europa.eu/api/v5_2"

    # Satellite imagery
    planet_api_key: str = ""
    sentinel_hub_client_id: str = ""
    sentinel_hub_client_secret: str = ""

    # Ordinances
    municode_api_key: str = ""

    @classmethod
    def from_env(cls) -> DataSourceConfig:
        """Load from environment variables."""
        return cls(
            regrid_api_key=os.getenv("REGRID_API_KEY", ""),
            eia_api_key=os.getenv("EIA_API_KEY", ""),
            nsrdb_api_key=os.getenv("NSRDB_API_KEY", ""),
            planet_api_key=os.getenv("PLANET_API_KEY", ""),
            sentinel_hub_client_id=os.getenv("SENTINEL_HUB_CLIENT_ID", ""),
            sentinel_hub_client_secret=os.getenv("SENTINEL_HUB_CLIENT_SECRET", ""),
        )


@dataclass
class AgentConfig:
    """Agent orchestration configuration."""
    # Timeouts
    agent_timeout_seconds: float = 60.0
    swarm_timeout_seconds: float = 120.0
    orchestrator_timeout_seconds: float = 300.0

    # Parallelism
    max_parallel_agents: int = 10
    max_parallel_swarms: int = 4

    # Human-in-the-loop
    default_approval_timeout_hours: float = 24.0
    escalation_email: str = ""

    # Approval thresholds
    fatal_flaw_score_threshold: float = 30.0
    high_value_score_threshold: float = 90.0
    cost_approval_threshold: float = 5_000_000.0  # $5M

    # Retries
    max_agent_retries: int = 2
    retry_delay_seconds: float = 2.0


@dataclass
class ScoringConfig:
    """Site scoring configuration."""
    # Weights (must sum to 1.0)
    permitting_weight: float = 0.30
    grid_weight: float = 0.30
    environmental_weight: float = 0.20
    land_weight: float = 0.10
    financial_weight: float = 0.10

    # Thresholds
    excellent_threshold: float = 90.0
    good_threshold: float = 75.0
    moderate_threshold: float = 60.0
    challenging_threshold: float = 40.0
    poor_threshold: float = 20.0

    # Fatal flaws
    fatal_flaw_conditions: List[str] = field(default_factory=lambda: [
        "solar_prohibited",
        "active_moratorium",
        "no_grid_access",
        "critical_habitat",
        "section_404_major",
    ])

    def validate_weights(self) -> bool:
        """Ensure weights sum to 1.0."""
        total = (
            self.permitting_weight +
            self.grid_weight +
            self.environmental_weight +
            self.land_weight +
            self.financial_weight
        )
        return abs(total - 1.0) < 0.001


@dataclass
class APIConfig:
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # CORS
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000"])

    # Authentication
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Rate limiting
    rate_limit_per_minute: int = 100
    rate_limit_burst: int = 20

    # Docs
    docs_enabled: bool = True
    openapi_url: str = "/openapi.json"

    @classmethod
    def from_env(cls) -> APIConfig:
        """Load from environment variables."""
        return cls(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            debug=os.getenv("API_DEBUG", "false").lower() == "true",
            jwt_secret=os.getenv("JWT_SECRET", ""),
            cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
        )


@dataclass
class MLConfig:
    """Machine learning model configuration."""
    # Model paths
    model_dir: str = "./models"

    # PowerGNN (grid analysis)
    grid_gnn_model_path: str = ""
    grid_gnn_enabled: bool = False

    # Satellite segmentation
    satellite_model_path: str = ""
    satellite_model_enabled: bool = False

    # Solar resource
    solar_model_path: str = ""
    solar_model_enabled: bool = False

    # Inference
    batch_size: int = 32
    use_gpu: bool = False
    gpu_device_id: int = 0


@dataclass
class TerraJinkiConfig:
    """
    Master configuration for TerraJinki platform.

    Aggregates all component configurations and provides
    centralized access and validation.
    """
    environment: Environment = Environment.DEVELOPMENT
    app_name: str = "TerraJinki"
    version: str = "1.0.0"

    # Component configs
    llm: LLMConfig = field(default_factory=LLMConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    data_sources: DataSourceConfig = field(default_factory=DataSourceConfig)
    agents: AgentConfig = field(default_factory=AgentConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    api: APIConfig = field(default_factory=APIConfig)
    ml: MLConfig = field(default_factory=MLConfig)

    # Feature flags
    enable_satellite_analysis: bool = True
    enable_gnn_grid_analysis: bool = True
    enable_rag_ordinances: bool = True
    enable_human_in_loop: bool = True
    enable_realtime_updates: bool = True

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    @classmethod
    def from_env(cls) -> TerraJinkiConfig:
        """
        Load configuration from environment variables.

        Environment variables take precedence over defaults.
        """
        env_str = os.getenv("TERRAJINKI_ENV", "development").lower()
        environment = Environment(env_str) if env_str in [e.value for e in Environment] else Environment.DEVELOPMENT

        return cls(
            environment=environment,
            llm=LLMConfig.from_env(),
            database=DatabaseConfig.from_env(),
            data_sources=DataSourceConfig.from_env(),
            api=APIConfig.from_env(),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            enable_satellite_analysis=os.getenv("ENABLE_SATELLITE", "true").lower() == "true",
            enable_gnn_grid_analysis=os.getenv("ENABLE_GNN", "true").lower() == "true",
            enable_rag_ordinances=os.getenv("ENABLE_RAG", "true").lower() == "true",
            enable_human_in_loop=os.getenv("ENABLE_HITL", "true").lower() == "true",
        )

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of issues.

        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []

        # Check required API keys for production
        if self.environment == Environment.PRODUCTION:
            if not self.llm.anthropic_api_key:
                issues.append("ANTHROPIC_API_KEY is required in production")
            if not self.api.jwt_secret:
                issues.append("JWT_SECRET is required in production")

        # Validate scoring weights
        if not self.scoring.validate_weights():
            issues.append("Scoring weights must sum to 1.0")

        # Validate thresholds
        if self.agents.fatal_flaw_score_threshold >= self.agents.high_value_score_threshold:
            issues.append("Fatal flaw threshold must be less than high value threshold")

        return issues

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION

    def get_llm_model(self, tier: str = "analysis") -> str:
        """
        Get appropriate LLM model for the tier.

        Args:
            tier: One of 'orchestrator', 'analysis', 'fast'

        Returns:
            Model identifier string
        """
        if tier == "orchestrator":
            return self.llm.anthropic_model_orchestrator
        elif tier == "analysis":
            return self.llm.anthropic_model_analysis
        else:
            return self.llm.anthropic_model_fast


# Global config instance (lazy loaded)
_config: Optional[TerraJinkiConfig] = None


def get_config() -> TerraJinkiConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = TerraJinkiConfig.from_env()
    return _config


def set_config(config: TerraJinkiConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
