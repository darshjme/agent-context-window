# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-24

### Added
- `TokenCounter` — approximate token counting without API calls, model-specific ratios
- `ContextWindow` — sliding window conversation manager with auto-prune on overflow
- `ContentPrioritizer` — keyword + recency scoring and re-ranking of messages
- `ContextTruncator` — text truncation with `"end"`, `"start"`, `"middle"` strategies
- `fit_messages()` to trim message lists with system-message protection
- Zero runtime dependencies — pure Python 3.10+
- 59 pytest tests, all passing
