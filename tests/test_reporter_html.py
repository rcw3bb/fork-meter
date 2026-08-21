"""Tests for fork_meter.reporter.html_reporter."""

from pathlib import Path

from fork_meter.analyzer import AnalysisResult
from fork_meter.models import ComplexityResult
from fork_meter.reporter import html_reporter


def _result(complexity: int = 12) -> ComplexityResult:
    return ComplexityResult(
        "app.py", "Python", "function", "process", None, 1, 20, complexity
    )


def test_write_creates_file(tmp_path):
    out = tmp_path / "report.html"
    html_reporter.write(AnalysisResult(1, 1, [_result()]), 10, out)
    assert out.exists()


def test_write_contains_title(tmp_path):
    out = tmp_path / "r.html"
    html_reporter.write(AnalysisResult(1, 1, []), 10, out)
    content = out.read_text(encoding="utf-8")
    assert "fork-meter" in content


def test_write_shows_function_name(tmp_path):
    out = tmp_path / "r.html"
    res = ComplexityResult("a.py", "Python", "function", "my_func", None, 1, 10, 15)
    html_reporter.write(AnalysisResult(1, 1, [res]), 10, out)
    assert "my_func" in out.read_text(encoding="utf-8")


def test_write_empty_results_no_table(tmp_path):
    out = tmp_path / "r.html"
    html_reporter.write(AnalysisResult(2, 5, []), 10, out)
    content = out.read_text(encoding="utf-8")
    assert "<table" not in content
    assert "No functions exceed" in content


def test_write_creates_parent_directories(tmp_path):
    out = tmp_path / "sub" / "dir" / "report.html"
    html_reporter.write(AnalysisResult(0, 0, []), 10, out)
    assert out.exists()


def test_write_returns_resolved_path(tmp_path):
    out = tmp_path / "report.html"
    returned = html_reporter.write(AnalysisResult(0, 0, []), 10, out)
    assert isinstance(returned, Path)
    assert returned.is_absolute()


def test_write_threshold_in_output(tmp_path):
    out = tmp_path / "r.html"
    html_reporter.write(AnalysisResult(1, 5, []), 7, out)
    # Jinja2 autoescape renders '>' as '&gt;' inside {{ }} variables.
    assert "&gt; 7" in out.read_text(encoding="utf-8")
