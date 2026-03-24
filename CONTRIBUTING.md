# Contributing

Thank you for considering contributing to **agent-context-window**!

## Getting Started

1. Fork the repository and clone it locally.
2. Create a virtual environment and install dev dependencies:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   ```
3. Create a feature branch: `git checkout -b feat/my-feature`

## Code Style

- Follow PEP 8. Use type hints everywhere.
- Keep public methods documented with NumPy-style docstrings.
- No runtime dependencies allowed — stdlib only.

## Testing

All PRs must include tests. Run the suite with:
```bash
python -m pytest tests/ -v
```
Target: 100 % pass rate. Coverage additions are welcome.

## Pull Requests

- One logical change per PR.
- Write a clear description of *what* and *why*.
- Reference any related issues.

## Reporting Bugs

Open a GitHub issue with:
- Python version (`python --version`)
- Minimal reproducible example
- Expected vs actual output
