"""Tests for the fork_meter CLI entry point."""

from click.testing import CliRunner

from fork_meter.__main__ import main


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
    assert result.exit_code == 0
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
    assert result.exit_code == 0
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
