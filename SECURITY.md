# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.x     | ✅ |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report vulnerabilities privately by emailing the project maintainer or opening a GitHub Security Advisory.

Include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if known)

You should receive a response within 48 hours.

## Security Practices

### API Keys

- All API keys are stored in `.env` files excluded from version control.
- Never commit `.env` files to the repository.
- Use `.env.example` as a template with placeholder values.

### Dependencies

- Dependencies are reviewed regularly.
- Use `pip-audit` or `npm audit` to check for known vulnerabilities.
- Keep dependencies up to date with `dependabot` or similar tools.

### Network Security

- The search tool (`WebScraper`) blocks requests to private/internal IP ranges to prevent SSRF.
- All external API calls use HTTPS where available.

### Authentication

- API endpoints can be secured via auth middleware (see `backend/app/core/security.py`).
- JWT tokens use configurable secrets.
- Session management via Redis with TTL-based expiration.

## Dependency Vulnerability Disclosure

If you discover a vulnerability in a dependency:

1. Check if a patched version exists.
2. If not, report to the dependency maintainer.
3. Notify this project so we can update or replace the dependency.
