# Contributing to ARAMS

Thank you for considering contributing to ARAMS. We welcome contributions of all kinds — bug reports, feature requests, documentation, and code.

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold its terms.

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates.
2. Include a clear title and description.
3. Provide steps to reproduce, expected behavior, and actual behavior.
4. Include logs, screenshots, or API responses if relevant.

### Suggesting Features

1. Describe the problem you're solving.
2. Explain the proposed solution.
3. Mention alternatives you've considered.

### Pull Requests

1. Fork the repository and create a feature branch: `git checkout -b feature/my-feature`.
2. Make your changes following the existing code style.
3. Add or update tests as needed.
4. Run the test suite: `cd backend && python -m pytest`.
5. Ensure the frontend builds: `cd frontend && npm run build`.
6. Commit with a clear, descriptive message.
7. Push and open a pull request.

## Development Setup

See [README.md](README.md#installation) for local development setup instructions.

## Code Style

- Python: Follow PEP 8. Type hints are required for all public functions.
- TypeScript: Use strict mode. Define types for all props and state.
- Frontend: Match the existing Tailwind CSS design system. Avoid adding new CSS files unless necessary.

## Commit Messages

Use conventional commits:

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation
- `chore:` — maintenance, cleanup
- `refactor:` — code restructuring
- `test:` — test additions/changes

## Questions

Open a GitHub Discussion or issue for questions.
