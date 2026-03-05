# Contributing to ConsulApp

Thank you for your interest in contributing to ConsulApp! This document outlines our development workflow and conventions.

## Branch Workflow

We use a structured branching model:

```
main          <- Production-ready code (protected)
  |
  +-- dev     <- Integration branch for features (protected)
       |
       +-- feature/NNN-slug  <- Individual features
```

### Branch Naming

- **Feature branches**: `feature/NNN-description` where NNN is the issue/task number
  - Example: `feature/001-git-workflow`
  - Example: `feature/042-patient-search`

### Creating a Feature Branch

```bash
# Start from dev
git checkout dev
git pull origin dev

# Create feature branch
git checkout -b feature/NNN-description

# Work on your feature...

# Push and create PR
git push -u origin feature/NNN-description
gh pr create --base dev --title "feat: description" --body "..."
```

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks, dependencies, CI |

### Examples

```bash
git commit -m "feat(turnos): add conflict detection for overlapping appointments"
git commit -m "fix(auth): prevent session fixation on login"
git commit -m "docs: update API documentation"
git commit -m "test(pacientes): add search autocomplete tests"
```

## Pull Request Process

1. **Create PR to `dev`** (not `main`)
2. **Fill out the PR template** completely
3. **Ensure CI passes** (lint + tests)
4. **Request review** from at least one team member
5. **Address feedback** with additional commits (don't force-push)
6. **Squash merge** when approved

### PR Title Format

Use the same format as commits:
- `feat(scope): description`
- `fix(scope): description`

## Development Setup

```bash
# Clone and setup
git clone git@github.com:mateoadann/consul_app.git
cd consul_app

# Start with Docker (recommended)
make up
make seed  # Optional: load sample data

# Run tests
make docker-test
```

## Testing Requirements

- All new features must include tests
- All bug fixes must include a regression test
- Tests must pass before merging
- Maintain or improve code coverage

### Running Tests

```bash
# Full test suite in Docker
make docker-test

# Local tests (requires PostgreSQL)
export TEST_DATABASE_URL=postgresql+psycopg2://consul:consul@localhost:5432/consul_app_test
pytest -vv -rA

# Specific test
pytest tests/test_turnos.py -k test_solapamiento -vv
```

## Code Style

- Python: Follow PEP 8 (enforced by flake8)
- Templates: Use consistent indentation (2 spaces)
- JavaScript: No frameworks, vanilla JS with HTMX
- CSS: Mobile-first approach

## Questions?

Open an issue for questions about contributing or the codebase.
