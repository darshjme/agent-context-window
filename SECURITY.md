# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Yes    |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Email: darshjme@gmail.com with the subject line `[SECURITY] agent-context-window`.

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix

You will receive a response within 72 hours. We aim to release a patch within 14 days of confirmation.

## Scope

This library performs no network I/O, no file system writes, and no subprocess execution. It operates purely on in-memory string data. The attack surface is limited to:

- Malformed `messages` list input (handled via `.get()` with defaults)
- Extremely large strings causing memory exhaustion (caller's responsibility to bound inputs)
