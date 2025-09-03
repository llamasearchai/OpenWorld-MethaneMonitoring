from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .core.logging import LogConfig


class StorageSettings(BaseModel):
    backend: str = Field(default="memory", description="storage backend: memory|jsonl|postgres")
    jsonl_path: Optional[str] = Field(default=None, description="path for jsonl store")
    dsn: Optional[str] = Field(default=None, description="PostgreSQL DSN if using postgres")

    @field_validator("backend")
    @classmethod
    def validate_backend(cls, v: str) -> str:
        allowed_backends = {"memory", "jsonl", "postgres"}
        if v not in allowed_backends:
            raise ValueError(f"Backend must be one of {allowed_backends}, got: {v}")
        return v


class AlertSettings(BaseModel):
    slack_webhook_url: Optional[str] = None
    email_smtp_host: Optional[str] = None
    email_smtp_port: int = 25
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_use_tls: bool = False
    email_from: Optional[str] = None
    email_to: list[str] = Field(default_factory=list)

    @field_validator("email_smtp_port")
    @classmethod
    def validate_smtp_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError(f"SMTP port must be between 1 and 65535, got: {v}")
        return v

    @field_validator("slack_webhook_url")
    @classmethod
    def validate_slack_webhook(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith("https://hooks.slack.com/"):
            raise ValueError("Slack webhook URL must start with 'https://hooks.slack.com/'")
        return v

    @field_validator("email_to")
    @classmethod
    def validate_email_addresses(cls, v: list[str]) -> list[str]:
        import re
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        for email in v:
            if not email_pattern.match(email):
                raise ValueError(f"Invalid email address: {email}")
        return v


class AnalyticsSettings(BaseModel):
    anomaly_method: str = Field(default="robust_z")
    anomaly_z_threshold: float = 3.5
    seasonal_period: int = 24

    @field_validator("anomaly_method")
    @classmethod
    def validate_anomaly_method(cls, v: str) -> str:
        allowed_methods = {"robust_z", "seasonal"}
        if v not in allowed_methods:
            raise ValueError(f"Anomaly method must be one of {allowed_methods}, got: {v}")
        return v

    @field_validator("anomaly_z_threshold")
    @classmethod
    def validate_z_threshold(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"Z-threshold must be positive, got: {v}")
        return v

    @field_validator("seasonal_period")
    @classmethod
    def validate_seasonal_period(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"Seasonal period must be positive, got: {v}")
        return v


class ComplianceSettings(BaseModel):
    threshold_kg_per_h: float = 10.0
    remediation_due_days: int = 7

    @field_validator("threshold_kg_per_h")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"Threshold must be positive, got: {v}")
        return v

    @field_validator("remediation_due_days")
    @classmethod
    def validate_due_days(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"Remediation due days must be positive, got: {v}")
        return v


class ServerSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError(f"Port must be between 1 and 65535, got: {v}")
        return v


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OWM_", env_file=None, extra="ignore")

    environment: str = Field(default="dev")
    storage: StorageSettings = Field(default_factory=StorageSettings)
    alerts: AlertSettings = Field(default_factory=AlertSettings)
    analytics: AnalyticsSettings = Field(default_factory=AnalyticsSettings)
    compliance: ComplianceSettings = Field(default_factory=ComplianceSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    logging: LogConfig = Field(default_factory=LogConfig)

    config_file: Optional[str] = Field(default=None, description="Optional path to TOML config")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed_envs = {"dev", "test", "staging", "prod", "production"}
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}, got: {v}")
        return v

    @classmethod
    def from_file_and_env(cls, config_file: Optional[str] = None) -> AppSettings:
        # If a config file is provided, let pydantic-settings parse it (TOML or env-only)
        if config_file:
            return cls.model_validate_json(_load_toml_as_json(config_file))
        return cls()


def _load_toml_as_json(path: str) -> str:
    # Use stdlib tomllib if available (py311+); otherwise fall back to "tomli" dependency
    try:
        import tomllib as _toml  # type: ignore[attr-defined]
    except Exception:
        try:
            import tomli as _toml  # type: ignore
        except Exception as e:  # pragma: no cover - fallback/notice
            raise RuntimeError(
                "Reading TOML config requires Python 3.11+ (tomllib) or the 'tomli' package"
            ) from e
    import json
    from pathlib import Path

    data = _toml.loads(Path(path).read_text(encoding="utf-8"))
    # Normalize possible nested environment table like [environment]\nenvironment = "dev"
    if isinstance(data.get("environment"), dict) and "environment" in data["environment"]:
        env_value = data["environment"].get("environment")
        if isinstance(env_value, str):
            data["environment"] = env_value
    return json.dumps(data)


@lru_cache(maxsize=1)
def get_settings(config_file: Optional[str] = None) -> AppSettings:
    return AppSettings.from_file_and_env(config_file)
