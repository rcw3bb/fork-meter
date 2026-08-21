"""Tests for fork_meter.reporter.json_reporter."""

import json
from pathlib import Path

from fork_meter.analyzer import AnalysisResult
from fork_meter.models import ComplexityResult
from fork_meter.reporter import json_reporter


def _result(complexity: int = 12) -> ComplexityResult:
    return ComplexityResult(
        "foo.py", "Python", "function", "bar", None, 1, 10, complexity
    )


def test_write_creates_file(tmp_path):
    out = tmp_path / "report.json"
    json_reporter.write(AnalysisResult(1, 1, [_result()]), ["foo.py"], 10, out)
    assert out.exists()


def test_write_json_top_level_keys(tmp_path):
    out = tmp_path / "r.json"
    json_reporter.write(AnalysisResult(2, 5, [_result()]), ["src/"], 10, out)
    data = json.loads(out.read_text())
    assert "generated_at" in data
    assert data["version"]
    assert data["scan_paths"] == ["src/"]
    assert data["max_threshold"] == 10


def test_write_summary_counts(tmp_path):
    out = tmp_path / "r.json"
    json_reporter.write(AnalysisResult(3, 8, [_result(), _result()]), ["p/"], 10, out)
    summary = json.loads(out.read_text())["summary"]
    assert summary["files_scanned"] == 3
    assert summary["functions_analyzed"] == 8
    assert summary["above_threshold"] == 2


def test_write_result_fields(tmp_path):
    out = tmp_path / "r.json"
    res = ComplexityResult("a.py", "Python", "method", "run", "App", 5, 15, 12)
    json_reporter.write(AnalysisResult(1, 1, [res]), ["a.py"], 10, out)
    record = json.loads(out.read_text())["results"][0]
    assert record["file_path"] == "a.py"
    assert record["language"] == "Python"
    assert record["fragment_type"] == "method"
    assert record["name"] == "run"
    assert record["parent_class"] == "App"
    assert record["start_line"] == 5
    assert record["end_line"] == 15
    assert record["complexity"] == 12


def test_write_creates_parent_directories(tmp_path):
    out = tmp_path / "deep" / "nested" / "report.json"
    json_reporter.write(AnalysisResult(0, 0, []), [], 10, out)
    assert out.exists()


def test_write_empty_results(tmp_path):
    out = tmp_path / "empty.json"
    json_reporter.write(AnalysisResult(3, 10, []), ["src/"], 10, out)
    data = json.loads(out.read_text())
    assert data["summary"]["above_threshold"] == 0
    assert data["results"] == []


def test_write_returns_resolved_path(tmp_path):
    out = tmp_path / "report.json"
    returned = json_reporter.write(AnalysisResult(0, 0, []), [], 10, out)
    assert isinstance(returned, Path)
    assert returned.is_absolute()
