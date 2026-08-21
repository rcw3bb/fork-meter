# fork-meter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)

A command-line tool that measures cyclomatic complexity by counting decision points and branching paths in source code.

## Requirements

- Python `>=3.14`

## Installation

```bash
pip install fork-meter
```

## Supported Languages

| Language | Grammar |
|----------|---------|
| Python | tree-sitter-python |
| JavaScript | tree-sitter-javascript |
| TypeScript | tree-sitter-typescript |
| Java | tree-sitter-java |
| Go | tree-sitter-go |
| Gosu | tree-sitter-gosu |

## Usage

```
fork-meter [OPTIONS] PATHS...
```

`PATHS` may be files or directories; directories are scanned recursively.

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--max INT` | `10` | Report functions with complexity strictly above this value |
| `--output NAME` | `fork-meter-output` | Base name for output files (no extension) |
| `--output-dir DIR` | `<cwd>/reports` | Directory for output files |
| `--format [json\|html\|both]` | `both` | Output format |
| `--exclude PATTERN` | — | Glob pattern to exclude from scanning (repeatable) |
| `-V, --version` | | Show version and exit |
| `-h, --help` | | Show help and exit |

### Example

```bash
# Scan a project, flag anything above complexity 5, write HTML only
fork-meter src/ --max 5 --format html --exclude "**/*_test.py"
```

Output:

```
fork-meter done in 0.08s
  ✓ reports/fork-meter-output.html
```

## Complexity Scale

| Range | Colour | Risk |
|-------|--------|------|
| 1 – 5 | 🟢 Green | Low |
| 6 – 10 | 🟡 Yellow | Moderate |
| 11 – 15 | 🟠 Orange | High |
| 16 + | 🔴 Red | Critical |

## Output Formats

- **HTML** — self-contained interactive report with a sortable complexity table.
- **JSON** — machine-readable report suitable for CI integration.

## Configuration

`fork-meter` bootstraps its log/config directory automatically. Override the location with:

```bash
export FORK_METER_CONFIG_DIR=/path/to/dir
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

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
