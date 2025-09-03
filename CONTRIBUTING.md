# Contributing to OpenWorld Methane Monitoring

Thank you for your interest in contributing to OpenWorld Methane Monitoring! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Git
- Make (optional, but recommended)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/OpenWorld-MethaneMonitoring.git
   cd OpenWorld-MethaneMonitoring
   ```

2. **Set up Development Environment**
   ```bash
   # Using Make (recommended)
   make install-dev
   
   # Or manually
   pip install -e ".[dev]"
   ```

3. **Verify Installation**
   ```bash
   make test
   make lint
   make type-check
   ```

## Development Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Individual feature development
- `hotfix/*`: Critical bug fixes

### Making Changes

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow coding standards (see below)
   - Add tests for new functionality
   - Update documentation if needed

3. **Test Your Changes**
   ```bash
   make test          # Run all tests
   make lint          # Check code style
   make type-check    # Verify type annotations
   make format        # Auto-format code
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add amazing new feature"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create Pull Request via GitHub interface
   ```

## Coding Standards

### Code Style
- **Formatter**: Black with 100-character line length
- **Linter**: Ruff with strict settings
- **Import Sorting**: Automatic via Ruff
- **Type Checking**: MyPy with strict mode

### Code Quality Requirements
- **Type Hints**: All functions must have complete type annotations
- **Docstrings**: Required for all public APIs using Google style
- **Test Coverage**: Minimum 95% for new features
- **Security**: Input validation and sanitization required

### Example Code Structure
```python
"""Module docstring describing the module's purpose."""

from __future__ import annotations

import logging
from typing import Any

from ..core.logging import get_logger

logger = get_logger(__name__)


def process_data(data: list[dict[str, Any]], threshold: float = 5.0) -> list[dict[str, Any]]:
    """Process emission data with validation and filtering.
    
    Args:
        data: List of emission records to process.
        threshold: Minimum emission rate threshold in kg/h.
        
    Returns:
        Filtered list of emission records above threshold.
        
    Raises:
        ValueError: If data format is invalid.
    """
    if not data:
        logger.warning("Empty data provided to process_data")
        return []
    
    processed = []
    for record in data:
        if record.get("emission_rate_kg_per_h", 0) >= threshold:
            processed.append(record)
    
    logger.info(f"Processed {len(processed)}/{len(data)} records")
    return processed
```

### Commit Message Format
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or modifications
- `chore`: Build process or auxiliary tool changes

Examples:
- `feat(analytics): add seasonal anomaly detection`
- `fix(cli): handle missing config file gracefully`
- `docs(readme): update installation instructions`

## Testing Guidelines

### Test Structure
```
tests/
├── unit/                   # Unit tests
├── integration/           # Integration tests
├── conftest.py           # Pytest fixtures
└── test_*.py            # Test modules
```

### Writing Tests
```python
"""Test module for analytics functionality."""

import pytest
from datetime import datetime, timezone

from openworld_methane.analytics.anomaly import detect_anomalies
from openworld_methane.models import EmissionRecord


class TestAnomalyDetection:
    """Test suite for anomaly detection functionality."""
    
    @pytest.fixture
    def sample_records(self):
        """Create sample emission records for testing."""
        return [
            EmissionRecord(
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                site_id="site-1",
                region_id="region-1",
                emission_rate_kg_per_h=5.0,
                source="test"
            ),
            # ... more records
        ]
    
    def test_detect_anomalies_basic(self, sample_records):
        """Test basic anomaly detection functionality."""
        anomalies = detect_anomalies(sample_records, z_threshold=2.0)
        assert isinstance(anomalies, list)
        assert all(hasattr(a, 'record') for a in anomalies)
    
    def test_detect_anomalies_edge_cases(self):
        """Test anomaly detection with edge cases."""
        # Empty list
        assert detect_anomalies([]) == []
        
        # Single record
        single_record = [self.sample_records()[0]]
        result = detect_anomalies(single_record)
        assert len(result) == 0
```

### Test Commands
```bash
# Run all tests
make test

# Run with coverage report
make test-coverage

# Run specific test file
pytest tests/test_analytics.py -v

# Run specific test method
pytest tests/test_analytics.py::TestAnomalyDetection::test_detect_anomalies_basic -v

# Run tests with markers
pytest -m "not slow" -v
```

## Documentation

### Code Documentation
- **Module docstrings**: Describe module purpose and key components
- **Class docstrings**: Explain class purpose and usage
- **Function docstrings**: Use Google style with Args, Returns, Raises sections
- **Inline comments**: Explain complex logic or business rules

### API Documentation
- Update OpenAPI schema for new endpoints
- Include request/response examples
- Document error responses and status codes

### User Documentation
- Update README.md for user-facing changes
- Add examples to demonstrate new features
- Update configuration documentation

## Security Considerations

### Input Validation
- Validate all user inputs
- Sanitize file paths and URLs
- Check numeric ranges and formats
- Handle edge cases gracefully

### Error Handling
- Don't expose sensitive information in error messages
- Log security-relevant events
- Use structured logging for audit trails

### Example Security Implementation
```python
from ..core.security import validate_file_path, validate_email

def process_user_input(file_path: str, email: str) -> bool:
    """Process user input with security validation."""
    try:
        # Validate and sanitize inputs
        safe_path = validate_file_path(file_path, {'.csv', '.json'})
        safe_email = validate_email(email)
        
        # Process with validated inputs
        return True
        
    except ValueError as e:
        logger.warning(f"Invalid user input: {e}")
        return False
```

## Bug Reports

### Issue Template
When reporting bugs, please include:

1. **Environment Information**
   - OS and version
   - Python version
   - Package version
   - Dependencies versions

2. **Bug Description**
   - Clear, concise description
   - Expected vs actual behavior
   - Steps to reproduce

3. **Additional Context**
   - Error messages and stack traces
   - Log excerpts (sanitized)
   - Sample data (if relevant)

4. **Minimal Reproduction**
   ```python
   # Minimal code that reproduces the issue
   from openworld_methane import something
   
   # Steps that cause the bug
   result = something.process(bad_input)
   print(result)  # Shows unexpected behavior
   ```

## Feature Requests

### Enhancement Template
1. **Problem Description**
   - What problem does this solve?
   - Who would benefit from this feature?

2. **Proposed Solution**
   - Detailed description of the feature
   - API design (if applicable)
   - Configuration options needed

3. **Alternatives Considered**
   - Other solutions evaluated
   - Why this approach is preferred

4. **Implementation Notes**
   - Complexity assessment
   - Breaking changes required
   - Migration strategy

## Pull Request Guidelines

### PR Checklist
- [ ] Tests pass locally (`make test`)
- [ ] Code follows style guidelines (`make lint`)
- [ ] Type checking passes (`make type-check`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] No breaking changes (or clearly documented)

### PR Description Template
```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Additional Notes
Any additional information or context about the changes.
```

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes for significant contributions
- GitHub contributor statistics

## Getting Help

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Code Review**: Comments on pull requests

### Mentorship
New contributors can request mentorship by:
1. Opening an issue tagged with `help-wanted`
2. Joining GitHub Discussions
3. Commenting on `good-first-issue` labeled issues

## 📄 License

By contributing to OpenWorld Methane Monitoring, you agree that your contributions will be licensed under the same license as the project (Proprietary License).

---

Thank you for contributing to OpenWorld Methane Monitoring! Your efforts help improve environmental monitoring capabilities worldwide.