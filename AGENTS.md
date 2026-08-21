# AGENTS.md — fork-meter

## Purpose

`fork-meter` is a command-line tool that measures cyclomatic complexity by counting decision points and branching paths in source code.

## Project Tree

```
fork_meter/
    __init__.py          # Package init: bootstraps config dir, sets up logger, exposes CONF_DIR
    __main__.py          # CLI entry point (script: fork-meter)
    logging.ini          # Logging configuration (bundled as package resource)
tests/
    __init__.py
.gitattributes
.gitignore
.pylintrc
CHANGELOG.md
LICENSE
pyproject.toml
README.md
```

## Technology Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | `>=3.14` | Language |
| Poetry | `2.2` | Dependency management (PEP 621) |
| logenrich | `>=1.0.1,<2.0.0` | Logging |
| env-dir-bootstrap | `>=1.0.0,<2.0.0` | Config directory bootstrapping |
| Black | `>=26.5.1,<27.0.0` | Code formatting |
| Pylint | `>=4.0.5,<5.0.0` | Linting |
| Pytest | `>=9.0.3,<10.0.0` | Testing |
| Pytest-Cov | `>=7.1.0,<8.0.0` | Test coverage |

## Rules for AI Agents

### General

- Follow **SOLID** and **DRY** principles. Prefer composition over inheritance.
- Use dependency injection where applicable.
- Decompose large methods into smaller, focused private methods.

### Code Style

- **Naming**: `snake_case` for methods/variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- **Type hints**: required on all method arguments and return types.
- **Docstrings**: required on all modules, classes, and methods.
- **Author/since**: every module must have `:author: Ron Webb` and `:since: 1.0.0` in its docstring.
- **Imports**: use relative imports within the package.
- **Comments**: only where code is not self-explanatory; keep them to one short line.
- `typing` module deprecated types are forbidden — use `collections.abc` instead.
- Private/protected members must be prefixed with `_`.
- Max line length: 120 characters.
- Avoid `.env` files — use `FORK_METER_CONFIG_DIR` for configuration.

### Logging

- Import `setup_logger` from `logenrich`: `from logenrich import setup_logger`.
- Always pass `conf_dir=CONF_DIR` when calling `setup_logger`.
- Use `logging.getLogger(__name__)` inside modules; never call `setup_logger` again outside `__init__.py`.

### Testing

- Place test modules under `tests/`, mirroring the `fork_meter/` structure.
- Name test files `test_*.py`.
- Minimum test coverage: **90%**.
- Run: `poetry run pytest --cov=fork_meter tests --cov-report html`

### Linting & Formatting

- Run: `poetry run black fork_meter; poetry run pylint fork_meter`
- Pylint must score **10/10** — fix all warnings before committing.

### Dependency Management

- Add runtime deps: `poetry add <package>`
- Add dev deps: `poetry add --dev <package>`
- Keep `poetry.lock` committed to version control.
- `pyproject.toml` dependency format:
  ```toml
  dependencies = [
      "package (>=x.y.z,<x+1.0.0)"
  ]
  ```

### Changelog

- Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.
- Add an entry under the appropriate version heading for every user-visible change.

### Environment Variable

| Variable | Purpose |
|----------|---------|
| `FORK_METER_CONFIG_DIR` | Override the default configuration/log directory |
