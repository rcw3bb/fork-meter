# fork-meter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)

A command-line tool that measures cyclomatic complexity by counting decision points and branching paths in source code.

## Requirements

- Python `>=3.14`
- [Poetry](https://python-poetry.org/) `2.2`

## Installation

```bash
poetry install
```

## Usage

```bash
fork-meter
```

## Development

### Setup

```bash
poetry install
```

### Format and Lint

```bash
poetry run black fork_meter; poetry run pylint fork_meter
```

### Run Tests with Coverage

```bash
poetry run pytest --cov=fork_meter tests --cov-report html
```

## Configuration

By default, `fork-meter` bootstraps its configuration into a platform-appropriate directory. Override the location by setting the `FORK_METER_CONFIG_DIR` environment variable.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
