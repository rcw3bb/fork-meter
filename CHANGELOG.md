# Changelog

## 1.2.0 - 2026-09-12

### Added

- `--target-list` CLI flag: treats the positional `PATHS` argument as a single existing file
  listing target paths (files and/or directories), one per line (blank lines and `#`-comment
  lines skipped), instead of separate command-line path arguments.
- `config.ini` — new bundled default file (seeded into `FORK_METER_CONFIG_DIR` like
  `logging.ini`/`fm_ignore`) with an `[override]` section; its `ignore-file` key names the file
  used in place of `fm_ignore`, resolved relative to `FORK_METER_CONFIG_DIR`. Read via a new
  `Config` class in `fork_meter/config.py`.
- `_load_ignore_file()` now falls back to the bundled `fm_ignore` (logging a warning) when the
  configured custom ignore filename is missing, instead of giving up immediately.

### Changed

- Bumped `braincraft` dependency to `>=1.3.1,<2.0.0`.

## 1.1.1 - 2026-09-05

### Fixed

- Reconfigure `stdout`/`stderr` to UTF-8 (with `errors="replace"`) before creating the Rich
  console, preventing `UnicodeEncodeError` crashes when output is piped/redirected by another
  process (e.g. a calling app capturing subprocess output on a non-UTF-8 codepage).

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
