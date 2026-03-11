# Skill Registry — consul_app

Generated: 2026-03-11

## User Skills

| Skill | Path | Context Trigger |
|-------|------|-----------------|
| go-testing | `~/.claude/skills/go-testing/SKILL.md` | Go tests, Bubbletea TUI testing |
| skill-creator | `~/.claude/skills/skill-creator/SKILL.md` | Creating new AI skills |

## Project Conventions

| Source | Path | Description |
|--------|------|-------------|
| CLAUDE.md | `CLAUDE.md` | Project instructions: architecture, commands, domain rules, git workflow |

## Notes

- No project-level skills detected (no `SKILL.md` in project tree outside `~/.claude/skills/`)
- No `.cursorrules`, `agents.md`, or other convention files found in project root
- Linting: flake8 (max-line-length=120, configured in CI only — no `.flake8` or `pyproject.toml`)
- Testing: pytest + pytest-flask, requires PostgreSQL (no SQLite support)
