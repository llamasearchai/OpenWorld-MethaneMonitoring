# OpenWorld Methane Monitoring

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checking](https://img.shields.io/badge/type%20checking-mypy-blue)](https://mypy.readthedocs.io/)

A comprehensive, production-ready Python toolkit and CLI for methane emissions monitoring, analysis, and reporting. Built for industrial-scale environmental monitoring with robust data processing, anomaly detection, compliance tracking, and real-time alerting capabilities.

## Features

### Data Processing & Storage
- **Multi-format Ingestion**: CSV and JSON data support with robust error handling
- **Intelligent Storage**: High-performance indexed JSONL storage for large datasets
- **Unit Normalization**: Automatic conversion between g/h, m3/h, and kg/h units
- **Timestamp Handling**: UTC normalization with support for multiple timezone formats

### Analytics & Monitoring
- **Anomaly Detection**: Robust Z-score and seasonal decomposition algorithms
- **Time-series Aggregation**: Flexible time window aggregation (minutes to days)
- **Real-time Dashboards**: ASCII terminal and web-based monitoring interfaces
- **Compliance Tracking**: Configurable threshold-based compliance rules

### Alerting & Integration
- **Multi-channel Alerts**: Slack webhook and SMTP email notifications
- **API Endpoints**: RESTful API with FastAPI for system integration
- **Structured Logging**: Production-ready JSON logging with configurable levels
- **Configuration Management**: Environment variables and TOML file support

### Production Features
- **Security**: Input validation, path traversal protection, and sanitization
- **Performance**: Indexed storage, optimized queries, and memory-efficient processing
- **Monitoring**: Health checks, metrics, and comprehensive error tracking
- **Testing**: 95%+ test coverage with integration and unit tests

## Requirements

- **Python**: 3.9 or higher
- **Dependencies**: Pydantic, FastAPI (optional), Uvicorn (optional)
- **Operating System**: Cross-platform (Linux, macOS, Windows)

## Installation

### Production Installation
```bash
pip install openworld-methane-monitoring
```

### Development Installation
```bash
git clone <repository-url>
cd OpenWorld-MethaneMonitoring
make install-dev
```

### Docker Installation
```bash
docker build -t owm .
docker run -p 8000:8000 owm serve data.json
```

## Quick Start

### 1. Generate Sample Data
```bash
# Create sample dataset with 1000 records
owm simulate sample_data.json --rows 1000 --sites 5 --regions 3
```

### 2. Analyze for Anomalies
```bash
# Detect anomalies with Z-score threshold of 3.5
owm analyze sample_data.json --z 3.5 --output anomalies.json
```

### 3. Generate Reports
```bash
# Create comprehensive compliance report
owm report sample_data.json --threshold 10.0 --output report.json
```

### 4. Start Monitoring
```bash
# Launch web dashboard
owm serve sample_data.json --port 8080

# Or start full API server
owm api sample_data.json --host 0.0.0.0 --port 8000
```

## Command Reference

### Data Generation & Ingestion
```bash
# Simulate realistic methane emission data
owm simulate output.json --rows 500 --sites 3 --spike-prob 0.1

# Ingest and normalize existing data
owm ingest raw_data.csv --output normalized.json

# Append to JSONL store
owm log input.json storage.jsonl
```

### Analysis & Processing
```bash
# Anomaly detection with seasonal analysis
owm analyze data.json --method seasonal --period 24 --z 2.5

# Time-series aggregation
owm aggregate data.json --window 1h --output hourly_stats.csv

# Query time ranges
owm query data.jsonl --start 2024-01-01T00:00:00Z --end 2024-01-02T00:00:00Z
```

### Monitoring & Alerting
```bash
# Real-time file monitoring
owm watch data.json --interval 10 --config config.toml

# Send anomaly alerts
owm notify data.json --slack-webhook-url https://hooks.slack.com/... \\
                     --email-to admin@company.com --smtp-host smtp.company.com
```

### Dashboards & Visualization
```bash
# ASCII dashboard in terminal
owm dashboard data.json

# Web dashboard
owm serve data.json --host 0.0.0.0 --port 8080

# Full REST API
owm api data.json --config production.toml
```

## Configuration

### Environment Variables
```bash
export OWM_ENVIRONMENT=production
export OWM_STORAGE__BACKEND=jsonl
export OWM_STORAGE__JSONL_PATH=/var/log/emissions.jsonl
export OWM_ALERTS__EMAIL_SMTP_HOST=smtp.company.com
export OWM_ALERTS__EMAIL_TO=["admin@company.com"]
```

### Configuration File (`config.toml`)
```toml
environment = "production"

[logging]
level = "INFO"
format = "json"
output = "/var/log/owm.log"

[storage]
backend = "jsonl"
jsonl_path = "/data/emissions.jsonl"

[alerts]
email_smtp_host = "smtp.company.com"
email_smtp_port = 587
email_use_tls = true
email_from = "monitoring@company.com"
email_to = ["admin@company.com", "ops@company.com"]
slack_webhook_url = "https://hooks.slack.com/services/..."

[analytics]
anomaly_method = "seasonal"
anomaly_z_threshold = 3.0
seasonal_period = 24

[compliance]
threshold_kg_per_h = 10.0
remediation_due_days = 7

[server]
host = "0.0.0.0"
port = 8000
```

Validate configuration:
```bash
owm config --file config.toml
```

## Architecture

### Core Components

#### Data Layer
- **Models**: Type-safe emission record definitions with Pydantic
- **Adapters**: CSV/JSON readers with validation and error handling
- **Storage**: Indexed JSONL store for high-performance queries

#### Processing Layer
- **Analytics**: Anomaly detection and statistical analysis
- **Aggregation**: Time-window summarization and metrics calculation
- **Compliance**: Rule evaluation and remediation tracking

#### Interface Layer
- **CLI**: Comprehensive command-line interface with argument validation
- **API**: RESTful endpoints for system integration
- **Dashboards**: Web and terminal-based monitoring interfaces

#### Infrastructure
- **Logging**: Structured JSON logging with contextual information
- **Configuration**: Hierarchical settings with validation
- **Security**: Input sanitization and path traversal protection

### Data Flow
```
Raw Data (CSV/JSON) → Ingestion → Validation → Normalization → Storage
                                                                  ↓
Dashboards ← API ← Analytics ← Processing ← Indexed JSONL Store
     ↓
  Alerts → Email/Slack
```

## API Reference

### Core Endpoints
- `GET /records` - Retrieve emission records with filtering
- `GET /anomalies` - Get detected anomalies
- `GET /summary` - Statistical summary of emissions data
- `GET /health` - System health check

### Query Parameters
- `start` / `end` - ISO timestamp range filtering
- `site_id` - Filter by monitoring site
- `region_id` - Filter by geographic region
- `limit` - Maximum records to return

### Example Usage
```bash
# Get recent anomalies
curl "http://localhost:8000/api/anomalies?start=2024-01-01T00:00:00Z"

# Site-specific data
curl "http://localhost:8000/api/records?site_id=site-1&limit=100"
```

## Development

### Setup Development Environment
```bash
# Clone and set up development environment
git clone <repository-url>
cd OpenWorld-MethaneMonitoring
make install-dev

# Run tests
make test

# Check code quality
make lint
make type-check

# Format code
make format
```

### Testing
```bash
# Run all tests with coverage
make test-coverage

# Run specific test categories
pytest tests/test_security.py -v
pytest tests/test_analytics.py::test_anomaly_detection -v

# Performance testing
pytest tests/test_performance.py --benchmark-only
```

### Quality Assurance
```bash
# Full quality check pipeline
make qa

# Individual checks
make lint        # Ruff linting
make type-check  # MyPy type checking  
make format      # Black formatting
make security    # Security vulnerability scan
```

## Security

### Input Validation
- Path traversal protection for file operations
- Email format validation for alerting
- URL scheme validation for webhooks
- Numeric range validation for configuration

### Data Protection
- No sensitive data logging
- Configurable data retention policies
- Secure credential handling
- Input sanitization for all user data

### Production Deployment
- Environment-based configuration isolation
- Structured logging for security monitoring
- Error handling without information disclosure
- Rate limiting for API endpoints

## Performance

### Optimization Features
- **Indexed Storage**: O(log n) query performance with automatic indexing
- **Memory Efficiency**: Streaming processing for large datasets
- **Caching**: Intelligent caching of frequently accessed data
- **Batch Processing**: Optimized bulk operations

### Benchmarks
- **Ingestion**: 10,000+ records/second on standard hardware
- **Query Performance**: Sub-100ms response times for indexed queries
- **Memory Usage**: <50MB for 1M record datasets
- **Storage Efficiency**: ~60% compression vs raw JSON

## Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Standards
- **Type Hints**: All functions must have complete type annotations
- **Documentation**: Docstrings required for all public APIs
- **Testing**: 95%+ test coverage for new features
- **Formatting**: Black code formatting enforced
- **Linting**: Ruff linting with strict rules

## License

This project is licensed under the Proprietary License - see the [LICENSE](LICENSE) file for details.

## Support

### Documentation
- **API Docs**: Available at `/docs` when running the API server
- **Examples**: See `examples/` directory for sample datasets and usage
- **Configuration**: Detailed configuration options in `config.example.toml`

### Issue Reporting
Please report issues with:
- **Environment details** (OS, Python version)
- **Complete error messages** and stack traces
- **Minimal reproduction cases** when possible
- **Expected vs actual behavior** descriptions

### Community
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Issues**: GitHub Issues for bug reports and feature requests
- **Security**: Report security issues privately to the maintainers

---

**OpenWorld Methane Monitoring** - Production-ready environmental monitoring for the modern world.