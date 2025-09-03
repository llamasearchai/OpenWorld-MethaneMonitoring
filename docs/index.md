# OpenWorld Methane Monitoring

OpenWorld Methane Monitoring is a modular toolkit for methane emissions data ingestion, analytics, alerting, and reporting.

## Quickstart

```
pip install -e .[dev]
owm simulate out.json --rows 100
owm analyze out.json --z 3.5
owm serve out.json
```

## Configuration

See `config.example.toml` and `owm config --file config.example.toml`.

