"""Security utilities and input validation for OpenWorld Methane Monitoring."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from .logging import get_logger

logger = get_logger("core.security")


def validate_file_path(path: str | Path, allowed_extensions: set[str] | None = None) -> Path:
    """Validate a file path for security and basic checks.
    
    Args:
        path: The file path to validate.
        allowed_extensions: Set of allowed file extensions (e.g., {'.csv', '.json'}).
        
    Returns:
        The validated Path object.
        
    Raises:
        ValueError: If the path is invalid or potentially dangerous.
    """
    if isinstance(path, str):
        path = Path(path)

    # Check for path traversal attempts
    resolved_path = path.resolve()

    # Basic path traversal check
    path_str = str(path)
    dangerous_patterns = ['../', '..\\', '../', '..\\\\']
    if any(pattern in path_str for pattern in dangerous_patterns):
        logger.warning(f"Path traversal attempt detected: {path}")
        raise ValueError(f"Path traversal not allowed: {path}")

    # Check extension if provided
    if allowed_extensions and resolved_path.suffix.lower() not in allowed_extensions:
        raise ValueError(f"File extension {resolved_path.suffix} not allowed. Allowed: {allowed_extensions}")

    logger.debug(f"Validated file path: {resolved_path}")
    return resolved_path


def validate_url(url: str, allowed_schemes: set[str] | None = None) -> str:
    """Validate a URL for basic security checks.
    
    Args:
        url: The URL to validate.
        allowed_schemes: Set of allowed schemes (e.g., {'https', 'http'}).
        
    Returns:
        The validated URL.
        
    Raises:
        ValueError: If the URL is invalid or uses a disallowed scheme.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")

    if not parsed.scheme or not parsed.netloc:
        raise ValueError("URL must have both scheme and netloc")

    if allowed_schemes and parsed.scheme.lower() not in allowed_schemes:
        raise ValueError(f"URL scheme '{parsed.scheme}' not allowed. Allowed: {allowed_schemes}")

    # Check for suspicious patterns
    suspicious_patterns = [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '::1',
        '169.254.',  # AWS metadata service
        '10.',       # Private networks (basic check)
        '192.168.',  # Private networks
        '172.16.',   # Private networks
    ]

    netloc_lower = parsed.netloc.lower()
    for pattern in suspicious_patterns:
        if pattern in netloc_lower:
            logger.warning(f"Potentially suspicious URL detected: {url}")
            break

    logger.debug(f"Validated URL: {url}")
    return url


def validate_email(email: str) -> str:
    """Validate an email address format.
    
    Args:
        email: The email address to validate.
        
    Returns:
        The validated email address.
        
    Raises:
        ValueError: If the email format is invalid.
    """
    if not email or not isinstance(email, str):
        raise ValueError("Email must be a non-empty string")

    # Basic email regex - not perfect but good enough for most cases
    email_pattern = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    email = email.strip()
    if not email_pattern.match(email):
        raise ValueError(f"Invalid email format: {email}")

    # Additional checks
    if len(email) > 254:  # RFC 5321 limit
        raise ValueError("Email address too long (max 254 characters)")

    local_part, domain = email.rsplit('@', 1)
    if len(local_part) > 64:  # RFC 5321 limit
        raise ValueError("Email local part too long (max 64 characters)")

    logger.debug(f"Validated email: {email}")
    return email


def validate_port(port: int | str) -> int:
    """Validate a network port number.
    
    Args:
        port: The port number to validate.
        
    Returns:
        The validated port as an integer.
        
    Raises:
        ValueError: If the port is invalid.
    """
    try:
        port_int = int(port)
    except (ValueError, TypeError):
        raise ValueError(f"Port must be an integer, got: {port}")

    if not (1 <= port_int <= 65535):
        raise ValueError(f"Port must be between 1 and 65535, got: {port_int}")

    # Warn about privileged ports
    if port_int < 1024:
        logger.warning(f"Using privileged port {port_int} (< 1024)")

    return port_int


def sanitize_string(input_str: str, max_length: int = 1000, allow_newlines: bool = False) -> str:
    """Sanitize a string for safe use.
    
    Args:
        input_str: The string to sanitize.
        max_length: Maximum allowed length.
        allow_newlines: Whether to allow newline characters.
        
    Returns:
        The sanitized string.
        
    Raises:
        ValueError: If the string is invalid.
    """
    if not isinstance(input_str, str):
        raise ValueError("Input must be a string")

    if len(input_str) > max_length:
        raise ValueError(f"String too long (max {max_length} characters)")

    # Remove control characters except tab and newline
    sanitized = ''.join(
        char for char in input_str
        if ord(char) >= 32 or char in '\t\n\r'
    )

    if not allow_newlines:
        sanitized = sanitized.replace('\n', ' ').replace('\r', ' ')

    # Remove excessive whitespace while preserving newlines if allowed
    if allow_newlines:
        # Preserve newlines but normalize other whitespace
        lines = sanitized.split('\n')
        sanitized = '\n'.join(' '.join(line.split()) for line in lines)
    else:
        sanitized = ' '.join(sanitized.split())

    return sanitized


def validate_site_id(site_id: str) -> str:
    """Validate a site ID for safety and consistency.
    
    Args:
        site_id: The site ID to validate.
        
    Returns:
        The validated site ID.
        
    Raises:
        ValueError: If the site ID is invalid.
    """
    if not site_id or not isinstance(site_id, str):
        raise ValueError("Site ID must be a non-empty string")

    site_id = site_id.strip()

    if not re.match(r'^[a-zA-Z0-9_-]+$', site_id):
        raise ValueError("Site ID must contain only alphanumeric characters, hyphens, and underscores")

    if len(site_id) > 50:
        raise ValueError("Site ID too long (max 50 characters)")

    return site_id


def validate_region_id(region_id: str) -> str:
    """Validate a region ID for safety and consistency.
    
    Args:
        region_id: The region ID to validate.
        
    Returns:
        The validated region ID.
        
    Raises:
        ValueError: If the region ID is invalid.
    """
    if not region_id or not isinstance(region_id, str):
        raise ValueError("Region ID must be a non-empty string")

    region_id = region_id.strip()

    if not re.match(r'^[a-zA-Z0-9_-]+$', region_id):
        raise ValueError("Region ID must contain only alphanumeric characters, hyphens, and underscores")

    if len(region_id) > 50:
        raise ValueError("Region ID too long (max 50 characters)")

    return region_id


def validate_emission_rate(rate: float | int | str) -> float:
    """Validate an emission rate value.
    
    Args:
        rate: The emission rate to validate.
        
    Returns:
        The validated emission rate as a float.
        
    Raises:
        ValueError: If the emission rate is invalid.
    """
    try:
        rate_float = float(rate)
    except (ValueError, TypeError):
        raise ValueError(f"Emission rate must be a number, got: {rate}")

    if rate_float < 0:
        raise ValueError(f"Emission rate must be non-negative, got: {rate_float}")

    if rate_float > 1000000:  # Arbitrary upper limit
        raise ValueError(f"Emission rate seems unrealistic (> 1,000,000 kg/h): {rate_float}")

    return rate_float


def safe_filename(filename: str, max_length: int = 255) -> str:
    """Create a safe filename by removing/replacing dangerous characters.
    
    Args:
        filename: The original filename.
        max_length: Maximum allowed filename length.
        
    Returns:
        A safe filename.
    """
    if not filename:
        return "unnamed_file"

    # Remove path components
    filename = Path(filename).name

    # Replace dangerous characters
    dangerous_chars = r'<>:"/\\|?*'
    for char in dangerous_chars:
        filename = filename.replace(char, '_')

    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)

    # Trim whitespace and dots from ends
    filename = filename.strip(' .')

    # Check if filename is empty or only consists of underscores/replacements
    if not filename or filename.replace('_', '').replace('.', '') == '':
        filename = "unnamed_file"

    # Truncate if too long
    if len(filename) > max_length:
        name, ext = Path(filename).stem, Path(filename).suffix
        max_name_len = max_length - len(ext)
        filename = name[:max_name_len] + ext

    return filename
