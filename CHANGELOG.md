# Changelog

## 1.1.0 - 2026-09-04

### Added

- Support for C, C++, C#, Rust, Kotlin, and Scala source files.
- Ignore-file support via `braincraft.IgnoreFile`, backed by a bundled `fm_ignore` file
  bootstrapped into `FORK_METER_CONFIG_DIR` (editable like `logging.ini`).
- `fork-meter` now exits with status code `1` when any function exceeds `--max` complexity.
- Live progress indicator showing how many files have been checked during a scan.

## 1.0.0 - 2026-08-21

### Added

- Initial release of fork-meter.
- Command-line interface via `fork-meter` script.
- Cyclomatic complexity measurement by counting decision points and branching paths in source code.
- Logging via `logenrich` with configurable log directory (`FORK_METER_CONFIG_DIR`).
- Configuration directory bootstrapping via `env-dir-bootstrap`.
