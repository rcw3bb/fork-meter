"""Tests for the fork_meter CLI entry point."""

import shutil
import subprocess
import sys
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from fork_meter.__main__ import _ensure_utf8_streams, _load_ignore_file, main

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
    assert _load_ignore_file() is None


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
