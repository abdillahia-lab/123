"""
Configuration management for Paces platform.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from loguru import logger


class LLMConfig(BaseModel):
    """LLM configuration."""
    provider: str = "anthropic"
    model: str = "claude-3-5-sonnet-20241022"
    api_key: str = ""
    temperature: float = 0.1
    max_tokens: int = 4096


class DatabaseConfig(BaseModel):
    """Database configuration."""
    type: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    database: str = "paces"
    username: str = "paces"
    password: str = ""


class APIConfig(BaseModel):
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    api_key_enabled: bool = False


class DataSourcesConfig(BaseModel):
    """External data sources configuration."""
    # Parcel data
    regrid_api_key: str = ""

    # Grid data
    eia_api_key: str = ""

    # Environmental data
    usfws_enabled: bool = True

    # Solar resource
    nsrdb_api_key: str = ""


class PacesConfig(BaseSettings):
    """Main Paces configuration."""
    name: str = "Paces"
    version: str = "2.0.0"
    environment: str = "development"
    log_level: str = "INFO"

    data_dir: Path = Path("./data")
    cache_dir: Path = Path("./cache")

    llm: LLMConfig = Field(default_factory=LLMConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    data_sources: DataSourcesConfig = Field(default_factory=DataSourcesConfig)

    class Config:
        env_prefix = "PACES_"
        env_nested_delimiter = "__"

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PacesConfig":
        """Load configuration from YAML file."""
        path = Path(path)
        if not path.exists():
            logger.warning(f"Config not found: {path}, using defaults")
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return cls.model_validate(data)

    def ensure_directories(self) -> None:
        """Create necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


def load_config(config_path: Optional[str] = None) -> PacesConfig:
    """Load Paces configuration."""
    if config_path:
        return PacesConfig.from_yaml(config_path)

    default_paths = [
        Path("configs/paces.yaml"),
        Path("/etc/paces/config.yaml"),
        Path.home() / ".paces" / "config.yaml",
    ]

    for path in default_paths:
        if path.exists():
            logger.info(f"Loading config from: {path}")
            return PacesConfig.from_yaml(path)

    logger.info("Using default configuration")
    return PacesConfig()
