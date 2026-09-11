"""Tests for the fork_meter CLI entry point."""

import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from fork_meter.__main__ import (
    _ensure_utf8_streams,
    _load_ignore_file,
    _read_target_list,
    main,
)

_FORK_METER_EXE = shutil.which("fork-meter")


@pytest.fixture
def target_path(tmp_path):
    """Return a temporary directory containing a single low-complexity Python file."""
    (tmp_path / "sample.py").write_bytes(b"def foo():\n    return 1\n")
    return tmp_path


def test_help_exits_zero():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0


def test_version_exits_zero():
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0


def test_basic_scan_json(tmp_path):
    (tmp_path / "sample.py").write_bytes(b"def foo():\n    return 1\n")
    result = CliRunner().invoke(
        main,
        [
            str(tmp_path),
            "--format",
            "json",
            "--output-dir",
            str(tmp_path),
            "--max",
            "0",
        ],
    )
    assert result.exit_code == 1
    assert (tmp_path / "fork-meter-output.json").exists()


def test_basic_scan_html(tmp_path):
    (tmp_path / "sample.py").write_bytes(b"def foo():\n    return 1\n")
    result = CliRunner().invoke(
        main,
        [
            str(tmp_path),
            "--format",
            "html",
            "--output-dir",
            str(tmp_path),
            "--max",
            "0",
        ],
    )
    assert result.exit_code == 1
    assert (tmp_path / "fork-meter-output.html").exists()


def test_no_results_above_threshold(tmp_path):
    (tmp_path / "sample.py").write_bytes(b"def foo():\n    return 1\n")
    result = CliRunner().invoke(
        main,
        [
            str(tmp_path),
            "--format",
            "json",
            "--output-dir",
            str(tmp_path),
            "--max",
            "100",
        ],
    )
    assert result.exit_code == 0


def test_custom_output_name(tmp_path):
    (tmp_path / "a.py").write_bytes(b"def foo():\n    pass\n")
    CliRunner().invoke(
        main,
        [
            str(tmp_path),
            "--format",
            "json",
            "--output-dir",
            str(tmp_path),
            "--output",
            "my-report",
        ],
    )
    assert (tmp_path / "my-report.json").exists()


def test_exit_code_zero_when_clean(tmp_path):
    (tmp_path / "sample.py").write_bytes(b"def foo():\n    return 1\n")
    result = CliRunner().invoke(
        main,
        [str(tmp_path), "--format", "json", "--output-dir", str(tmp_path)],
    )
    assert result.exit_code == 0


def test_exit_code_one_when_complex_block_found(tmp_path):
    source = "def foo(a):\n" + "".join(
        f"    if a == {i}:\n        pass\n" for i in range(15)
    )
    (tmp_path / "complex.py").write_bytes(source.encode("utf-8"))
    result = CliRunner().invoke(
        main,
        [str(tmp_path), "--format", "json", "--output-dir", str(tmp_path)],
    )
    assert result.exit_code == 1


def test_load_ignore_file_returns_ignore_file():
    ignore_file = _load_ignore_file()
    assert ignore_file is not None


def test_load_ignore_file_missing_returns_none(monkeypatch):
    monkeypatch.setattr("fork_meter.__main__.IGNORE_FILE", "/does/not/exist/.fm_ignore")
    monkeypatch.setattr(
        "fork_meter.__main__._config.get_ignore_file", lambda: "missing.ignore"
    )
    assert _load_ignore_file() is None


def test_load_ignore_file_falls_back_to_default_when_custom_missing(
    monkeypatch, caplog
):
    monkeypatch.setattr(
        "fork_meter.__main__._config.get_ignore_file", lambda: "missing.ignore"
    )
    with caplog.at_level("WARNING"):
        ignore_file = _load_ignore_file()
    assert ignore_file is not None
    assert "falling back to default" in caplog.text


def test_read_target_list_parses_one_path_per_line(tmp_path):
    list_file = tmp_path / "targets.txt"
    list_file.write_text("src\nlib\ntests\n", encoding="utf-8")

    result = _read_target_list(list_file)

    assert result == [Path("src"), Path("lib"), Path("tests")]


def test_read_target_list_skips_blank_and_comment_lines(tmp_path):
    list_file = tmp_path / "targets.txt"
    list_file.write_text("src\n\n# a comment\n  \nlib\n", encoding="utf-8")

    result = _read_target_list(list_file)

    assert result == [Path("src"), Path("lib")]


def test_main_target_list_scans_listed_targets(tmp_path):
    sample_file = tmp_path / "code.py"
    sample_file.write_bytes(b"def foo():\n    return 1\n")
    list_file = tmp_path / "targets.txt"
    list_file.write_text(f"{sample_file}\n", encoding="utf-8")

    result = CliRunner().invoke(
        main,
        [
            str(list_file),
            "--target-list",
            "--format",
            "json",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / "fork-meter-output.json").exists()


def test_main_target_list_rejects_multiple_paths(tmp_path):
    other_dir = tmp_path / "other"
    other_dir.mkdir()

    result = CliRunner().invoke(main, [str(tmp_path), str(other_dir), "--target-list"])

    assert result.exit_code != 0
    assert "--target-list" in result.output


def test_main_target_list_rejects_directory_path(tmp_path):
    result = CliRunner().invoke(main, [str(tmp_path), "--target-list"])

    assert result.exit_code != 0
    assert "--target-list" in result.output


def test_ensure_utf8_streams_reconfigures_non_utf8(monkeypatch):
    fake_stdout = MagicMock(encoding="cp1252")
    fake_stderr = MagicMock(encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", fake_stdout)
    monkeypatch.setattr(sys, "stderr", fake_stderr)

    _ensure_utf8_streams()

    fake_stdout.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")
    fake_stderr.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")


def test_ensure_utf8_streams_skips_already_utf8(monkeypatch):
    fake_stdout = MagicMock(encoding="utf-8")
    fake_stderr = MagicMock(encoding="UTF-8")
    monkeypatch.setattr(sys, "stdout", fake_stdout)
    monkeypatch.setattr(sys, "stderr", fake_stderr)

    _ensure_utf8_streams()

    fake_stdout.reconfigure.assert_not_called()
    fake_stderr.reconfigure.assert_not_called()


def test_ensure_utf8_streams_skips_streams_without_reconfigure(monkeypatch):
    class _NoReconfigure:  # pylint: disable=too-few-public-methods
        encoding = "cp1252"

    monkeypatch.setattr(sys, "stdout", _NoReconfigure())
    monkeypatch.setattr(sys, "stderr", _NoReconfigure())

    _ensure_utf8_streams()


@pytest.mark.skipif(
    _FORK_METER_EXE is None, reason="fork-meter console script not found on PATH"
)
def test_cli_subprocess_help_exits_zero():
    result = subprocess.run(
        [_FORK_METER_EXE, "--help"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0


@pytest.mark.skipif(
    _FORK_METER_EXE is None, reason="fork-meter console script not found on PATH"
)
def test_cli_subprocess_exits_zero_when_clean(target_path):
    result = subprocess.run(
        [
            _FORK_METER_EXE,
            str(target_path),
            "--format",
            "json",
            "--output-dir",
            str(target_path),
            "--max",
            "10",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    assert (target_path / "fork-meter-output.json").exists()


@pytest.mark.skipif(
    _FORK_METER_EXE is None, reason="fork-meter console script not found on PATH"
)
def test_cli_subprocess_exits_one_when_complex(target_path):
    result = subprocess.run(
        [
            _FORK_METER_EXE,
            str(target_path),
            "--format",
            "json",
            "--output-dir",
            str(target_path),
            "--max",
            "0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "UnicodeEncodeError" not in result.stderr
    assert (target_path / "fork-meter-output.json").exists()
