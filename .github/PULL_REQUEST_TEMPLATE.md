# Pull Request

## Description

Brief description of the changes made in this PR.

## Type of Change

Please select the relevant option(s):

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to change)
- [ ] 📚 Documentation update
- [ ] 🎨 Code style/formatting changes
- [ ] ♻️ Code refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] 🧪 Test additions or improvements
- [ ] 🔧 Build/CI changes
- [ ] 🔒 Security improvements

## Related Issues

Closes #(issue number)
Fixes #(issue number)
Related to #(issue number)

## Changes Made

### Core Changes
- [ ] Modified core functionality in `openworld_methane/`
- [ ] Updated CLI commands in `cli.py`
- [ ] Changed data models in `models.py`
- [ ] Updated configuration in `config.py`

### Specific Changes
- **File 1**: Description of changes
- **File 2**: Description of changes
- **File 3**: Description of changes

## Testing

### Test Coverage
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All existing tests pass

### Test Results
```bash
# Paste test output here
$ python -m pytest tests/ -v
```

### Manual Testing Steps
1. Step 1: Description
2. Step 2: Description
3. Step 3: Expected result

## Code Quality

### Checklist
- [ ] Code follows the project style guidelines
- [ ] Self-review of code completed
- [ ] Code is well-commented, particularly in hard-to-understand areas
- [ ] Type hints are complete and accurate
- [ ] No linting errors (`ruff check`)
- [ ] Code is properly formatted (`black`)
- [ ] Type checking passes (`mypy`)

### Performance Impact
- [ ] No performance impact
- [ ] Improves performance
- [ ] Minor performance regression (justified)
- [ ] Significant performance regression (requires discussion)

**Performance details:**
(If applicable, describe performance changes with benchmarks)

## Documentation

- [ ] Updated README.md if needed
- [ ] Updated CONTRIBUTING.md if needed
- [ ] Added/updated docstrings for new functions
- [ ] Updated configuration examples
- [ ] Added examples for new features
- [ ] Updated API documentation

## Breaking Changes

**Are there any breaking changes?**
- [ ] No breaking changes
- [ ] Yes, breaking changes (describe below)

**If yes, describe the breaking changes:**
- What existing functionality changes
- How users can migrate their code/config
- Deprecation notices added

## Security Considerations

- [ ] No security implications
- [ ] Security review completed
- [ ] Input validation added/updated
- [ ] No sensitive data exposed in logs
- [ ] Dependencies checked for vulnerabilities

## Deployment Notes

**Special deployment considerations:**
- [ ] Database migrations required
- [ ] Configuration changes required
- [ ] Environment variable changes
- [ ] New dependencies added

**Configuration changes:**
```toml
# Example of new configuration options
[new_section]
option = "value"
```

## Screenshots (if applicable)

<!-- Add screenshots of UI changes, CLI output, etc. -->

## Additional Context

Add any other context about the pull request here:
- Why these changes were necessary
- Alternatives considered
- Future improvements planned

## Review Checklist

### For Reviewers
Please verify:
- [ ] Code quality and style
- [ ] Test coverage adequacy
- [ ] Documentation completeness
- [ ] Performance implications
- [ ] Security considerations
- [ ] Backward compatibility

### Author's Self-Review
- [ ] I have reviewed my own code
- [ ] I have tested the changes locally
- [ ] I have considered edge cases
- [ ] I have updated relevant documentation
- [ ] I have added appropriate tests

---

**Additional Notes for Reviewers:**
<!-- Any specific areas you'd like reviewers to focus on -->