---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: 'bug'
assignees: ''
---

## Bug Description

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:
1. Install package version: `pip show openworld-methane-monitoring`
2. Run command: `owm ...`
3. Use input data: (attach sample file if applicable)
4. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

A clear and concise description of what actually happened.

## Error Output

```
Paste the complete error message and stack trace here
```

## Environment Information

**Please complete the following information:**
- OS: [e.g., Ubuntu 22.04, macOS 14.0, Windows 11]
- Python version: [e.g., 3.9.18]
- Package version: [e.g., 0.2.0]
- Installation method: [e.g., pip, conda, from source]

**Dependencies (if relevant):**
Run `pip freeze` and paste relevant package versions:
```
openworld-methane-monitoring==0.2.0
pydantic==2.7.0
...
```

## Sample Data

If applicable, provide a minimal sample dataset that reproduces the issue:

```json
[
  {
    "timestamp": "2024-01-01T12:00:00Z",
    "site_id": "test-site",
    "region_id": "test-region", 
    "value": 5.5,
    "unit": "kg/h"
  }
]
```

## Configuration

If using a configuration file, please provide the relevant sections (with sensitive data removed):

```toml
[storage]
backend = "jsonl"
jsonl_path = "/data/emissions.jsonl"

[analytics]
anomaly_method = "robust_z"
```

## Additional Context

Add any other context about the problem here, such as:
- When did this start happening?
- Does it happen consistently?
- Any recent changes to your setup?
- Workarounds you've tried

## Logs

If possible, run with debug logging and include relevant log output:

```bash
export OWM_LOGGING__LEVEL=DEBUG
owm your-command-here
```

```
Paste debug logs here (sanitized of any sensitive information)
```

## Possible Solution

If you have ideas about what might be causing the issue or how to fix it, please share them here.

## Related Issues

Link any related issues or discussions:
- #123
- #456