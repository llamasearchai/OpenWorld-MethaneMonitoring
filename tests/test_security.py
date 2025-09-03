"""Tests for security utilities."""

from pathlib import Path

import pytest

from openworld_methane.core.security import (
    safe_filename,
    sanitize_string,
    validate_email,
    validate_emission_rate,
    validate_file_path,
    validate_port,
    validate_region_id,
    validate_site_id,
    validate_url,
)


class TestValidateFilePath:
    def test_valid_path(self):
        path = validate_file_path("/tmp/test.csv", {".csv"})
        assert isinstance(path, Path)
        assert path.name == "test.csv"

    def test_path_traversal(self):
        with pytest.raises(ValueError, match="Path traversal not allowed"):
            validate_file_path("../etc/passwd")

    def test_invalid_extension(self):
        with pytest.raises(ValueError, match="File extension .txt not allowed"):
            validate_file_path("/tmp/test.txt", {".csv", ".json"})

    def test_string_to_path_conversion(self):
        path = validate_file_path("test.csv", {".csv"})
        assert isinstance(path, Path)


class TestValidateUrl:
    def test_valid_https_url(self):
        url = validate_url("https://example.com", {"https"})
        assert url == "https://example.com"

    def test_invalid_scheme(self):
        with pytest.raises(ValueError, match="URL scheme 'ftp' not allowed"):
            validate_url("ftp://example.com", {"https"})

    def test_missing_netloc(self):
        with pytest.raises(ValueError, match="URL must have both scheme and netloc"):
            validate_url("https://")

    def test_suspicious_localhost(self):
        # Should not raise but may log warning
        url = validate_url("https://localhost:8000")
        assert url == "https://localhost:8000"

    def test_empty_url(self):
        with pytest.raises(ValueError, match="URL must be a non-empty string"):
            validate_url("")


class TestValidateEmail:
    def test_valid_email(self):
        email = validate_email("test@example.com")
        assert email == "test@example.com"

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email("invalid-email")

    def test_too_long(self):
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValueError, match="Email address too long"):
            validate_email(long_email)

    def test_long_local_part(self):
        long_local = "a" * 70 + "@example.com"
        with pytest.raises(ValueError, match="Email local part too long"):
            validate_email(long_local)

    def test_empty_email(self):
        with pytest.raises(ValueError, match="Email must be a non-empty string"):
            validate_email("")


class TestValidatePort:
    def test_valid_port(self):
        port = validate_port(8080)
        assert port == 8080

    def test_string_port(self):
        port = validate_port("8080")
        assert port == 8080

    def test_port_too_low(self):
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            validate_port(0)

    def test_port_too_high(self):
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            validate_port(65536)

    def test_invalid_port_type(self):
        with pytest.raises(ValueError, match="Port must be an integer"):
            validate_port("invalid")


class TestSanitizeString:
    def test_basic_sanitization(self):
        result = sanitize_string("hello world")
        assert result == "hello world"

    def test_remove_control_chars(self):
        result = sanitize_string("hello\x00\x01world")
        assert result == "helloworld"

    def test_remove_newlines(self):
        result = sanitize_string("hello\nworld")
        assert result == "hello world"

    def test_allow_newlines(self):
        result = sanitize_string("hello\nworld", allow_newlines=True)
        assert result == "hello\nworld"

    def test_too_long(self):
        with pytest.raises(ValueError, match="String too long"):
            sanitize_string("a" * 1001)

    def test_excessive_whitespace(self):
        result = sanitize_string("hello    world   ")
        assert result == "hello world"


class TestValidateSiteId:
    def test_valid_site_id(self):
        site_id = validate_site_id("site-123")
        assert site_id == "site-123"

    def test_with_underscores(self):
        site_id = validate_site_id("site_123")
        assert site_id == "site_123"

    def test_invalid_characters(self):
        with pytest.raises(ValueError, match="must contain only alphanumeric"):
            validate_site_id("site@123")

    def test_too_long(self):
        with pytest.raises(ValueError, match="Site ID too long"):
            validate_site_id("a" * 51)

    def test_empty_site_id(self):
        with pytest.raises(ValueError, match="Site ID must be a non-empty string"):
            validate_site_id("")


class TestValidateRegionId:
    def test_valid_region_id(self):
        region_id = validate_region_id("region-123")
        assert region_id == "region-123"

    def test_invalid_characters(self):
        with pytest.raises(ValueError, match="must contain only alphanumeric"):
            validate_region_id("region@123")

    def test_too_long(self):
        with pytest.raises(ValueError, match="Region ID too long"):
            validate_region_id("a" * 51)


class TestValidateEmissionRate:
    def test_valid_rate(self):
        rate = validate_emission_rate(5.5)
        assert rate == 5.5

    def test_string_rate(self):
        rate = validate_emission_rate("5.5")
        assert rate == 5.5

    def test_negative_rate(self):
        with pytest.raises(ValueError, match="Emission rate must be non-negative"):
            validate_emission_rate(-1.0)

    def test_unrealistic_rate(self):
        with pytest.raises(ValueError, match="Emission rate seems unrealistic"):
            validate_emission_rate(2000000)

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="Emission rate must be a number"):
            validate_emission_rate("invalid")


class TestSafeFilename:
    def test_basic_filename(self):
        result = safe_filename("test.txt")
        assert result == "test.txt"

    def test_dangerous_characters(self):
        result = safe_filename('test<>:"/\\|?*.txt')
        assert result == "____.txt"  # Dangerous chars replaced with underscores

    def test_path_components(self):
        result = safe_filename("/path/to/file.txt")
        assert result == "file.txt"

    def test_empty_filename(self):
        result = safe_filename("")
        assert result == "unnamed_file"

    def test_only_dangerous_chars(self):
        result = safe_filename("<>:")
        assert result == "unnamed_file"

    def test_too_long_filename(self):
        long_name = "a" * 300 + ".txt"
        result = safe_filename(long_name, max_length=255)
        assert len(result) <= 255
        assert result.endswith(".txt")

    def test_whitespace_and_dots(self):
        result = safe_filename("  test.txt  ...")
        assert result == "test.txt"
