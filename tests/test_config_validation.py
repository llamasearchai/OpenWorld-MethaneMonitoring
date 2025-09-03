"""Tests for configuration validation."""

import pytest
from pydantic import ValidationError

from openworld_methane.config import (
    AlertSettings,
    AnalyticsSettings,
    AppSettings,
    ComplianceSettings,
    ServerSettings,
    StorageSettings,
)


class TestStorageSettings:
    def test_valid_backends(self):
        """Test valid backend types."""
        for backend in ["memory", "jsonl", "postgres"]:
            settings = StorageSettings(backend=backend)
            assert settings.backend == backend

    def test_invalid_backend(self):
        """Test invalid backend type."""
        with pytest.raises(ValidationError) as exc_info:
            StorageSettings(backend="invalid")
        assert "Backend must be one of" in str(exc_info.value)

    def test_default_values(self):
        """Test default values."""
        settings = StorageSettings()
        assert settings.backend == "memory"
        assert settings.jsonl_path is None
        assert settings.dsn is None


class TestAlertSettings:
    def test_valid_smtp_port(self):
        """Test valid SMTP port validation."""
        settings = AlertSettings(email_smtp_port=587)
        assert settings.email_smtp_port == 587

    def test_invalid_smtp_port_low(self):
        """Test invalid SMTP port (too low)."""
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings(email_smtp_port=0)
        assert "SMTP port must be between 1 and 65535" in str(exc_info.value)

    def test_invalid_smtp_port_high(self):
        """Test invalid SMTP port (too high)."""
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings(email_smtp_port=70000)
        assert "SMTP port must be between 1 and 65535" in str(exc_info.value)

    def test_valid_slack_webhook(self):
        """Test valid Slack webhook URL."""
        url = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
        settings = AlertSettings(slack_webhook_url=url)
        assert settings.slack_webhook_url == url

    def test_invalid_slack_webhook(self):
        """Test invalid Slack webhook URL."""
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings(slack_webhook_url="https://example.com/webhook")
        assert "Slack webhook URL must start with" in str(exc_info.value)

    def test_valid_email_addresses(self):
        """Test valid email address validation."""
        emails = ["test@example.com", "user.name+tag@domain.co.uk"]
        settings = AlertSettings(email_to=emails)
        assert settings.email_to == emails

    def test_invalid_email_addresses(self):
        """Test invalid email address validation."""
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings(email_to=["invalid-email"])
        assert "Invalid email address" in str(exc_info.value)

    def test_default_values(self):
        """Test default values."""
        settings = AlertSettings()
        assert settings.email_smtp_port == 25
        assert settings.email_use_tls is False
        assert settings.email_to == []


class TestAnalyticsSettings:
    def test_valid_anomaly_methods(self):
        """Test valid anomaly detection methods."""
        for method in ["robust_z", "seasonal"]:
            settings = AnalyticsSettings(anomaly_method=method)
            assert settings.anomaly_method == method

    def test_invalid_anomaly_method(self):
        """Test invalid anomaly detection method."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyticsSettings(anomaly_method="invalid")
        assert "Anomaly method must be one of" in str(exc_info.value)

    def test_valid_z_threshold(self):
        """Test valid Z-threshold."""
        settings = AnalyticsSettings(anomaly_z_threshold=2.5)
        assert settings.anomaly_z_threshold == 2.5

    def test_invalid_z_threshold(self):
        """Test invalid Z-threshold (negative)."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyticsSettings(anomaly_z_threshold=-1.0)
        assert "Z-threshold must be positive" in str(exc_info.value)

    def test_valid_seasonal_period(self):
        """Test valid seasonal period."""
        settings = AnalyticsSettings(seasonal_period=48)
        assert settings.seasonal_period == 48

    def test_invalid_seasonal_period(self):
        """Test invalid seasonal period."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyticsSettings(seasonal_period=-5)
        assert "Seasonal period must be positive" in str(exc_info.value)

    def test_default_values(self):
        """Test default values."""
        settings = AnalyticsSettings()
        assert settings.anomaly_method == "robust_z"
        assert settings.anomaly_z_threshold == 3.5
        assert settings.seasonal_period == 24


class TestComplianceSettings:
    def test_valid_threshold(self):
        """Test valid threshold."""
        settings = ComplianceSettings(threshold_kg_per_h=15.0)
        assert settings.threshold_kg_per_h == 15.0

    def test_invalid_threshold(self):
        """Test invalid threshold (negative)."""
        with pytest.raises(ValidationError) as exc_info:
            ComplianceSettings(threshold_kg_per_h=-5.0)
        assert "Threshold must be positive" in str(exc_info.value)

    def test_valid_due_days(self):
        """Test valid remediation due days."""
        settings = ComplianceSettings(remediation_due_days=14)
        assert settings.remediation_due_days == 14

    def test_invalid_due_days(self):
        """Test invalid remediation due days."""
        with pytest.raises(ValidationError) as exc_info:
            ComplianceSettings(remediation_due_days=0)
        assert "Remediation due days must be positive" in str(exc_info.value)

    def test_default_values(self):
        """Test default values."""
        settings = ComplianceSettings()
        assert settings.threshold_kg_per_h == 10.0
        assert settings.remediation_due_days == 7


class TestServerSettings:
    def test_valid_port(self):
        """Test valid server port."""
        settings = ServerSettings(port=8080)
        assert settings.port == 8080

    def test_invalid_port_low(self):
        """Test invalid server port (too low)."""
        with pytest.raises(ValidationError) as exc_info:
            ServerSettings(port=0)
        assert "Port must be between 1 and 65535" in str(exc_info.value)

    def test_invalid_port_high(self):
        """Test invalid server port (too high)."""
        with pytest.raises(ValidationError) as exc_info:
            ServerSettings(port=70000)
        assert "Port must be between 1 and 65535" in str(exc_info.value)

    def test_default_values(self):
        """Test default values."""
        settings = ServerSettings()
        assert settings.host == "127.0.0.1"
        assert settings.port == 8000


class TestAppSettings:
    def test_valid_environment(self):
        """Test valid environment values."""
        valid_envs = ["dev", "test", "staging", "prod", "production"]
        for env in valid_envs:
            settings = AppSettings(environment=env)
            assert settings.environment == env

    def test_invalid_environment(self):
        """Test invalid environment value."""
        with pytest.raises(ValidationError) as exc_info:
            AppSettings(environment="invalid")
        assert "Environment must be one of" in str(exc_info.value)

    def test_default_values(self):
        """Test default values for app settings."""
        settings = AppSettings()
        assert settings.environment == "dev"
        assert isinstance(settings.storage, StorageSettings)
        assert isinstance(settings.alerts, AlertSettings)
        assert isinstance(settings.analytics, AnalyticsSettings)
        assert isinstance(settings.compliance, ComplianceSettings)
        assert isinstance(settings.server, ServerSettings)

    def test_nested_validation(self):
        """Test that nested settings validation works."""
        with pytest.raises(ValidationError) as exc_info:
            AppSettings(
                storage={"backend": "invalid_backend"}
            )
        assert "Backend must be one of" in str(exc_info.value)

    def test_complex_valid_config(self):
        """Test a complex but valid configuration."""
        config_data = {
            "environment": "prod",
            "storage": {
                "backend": "jsonl",
                "jsonl_path": "/var/log/emissions.jsonl"
            },
            "alerts": {
                "email_smtp_port": 587,
                "email_use_tls": True,
                "email_to": ["admin@example.com", "ops@example.com"],
                "slack_webhook_url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
            },
            "analytics": {
                "anomaly_method": "seasonal",
                "anomaly_z_threshold": 2.0,
                "seasonal_period": 48
            },
            "compliance": {
                "threshold_kg_per_h": 20.0,
                "remediation_due_days": 14
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8080
            }
        }

        settings = AppSettings(**config_data)

        assert settings.environment == "prod"
        assert settings.storage.backend == "jsonl"
        assert settings.alerts.email_smtp_port == 587
        assert settings.analytics.anomaly_method == "seasonal"
        assert settings.compliance.threshold_kg_per_h == 20.0
        assert settings.server.port == 8080
