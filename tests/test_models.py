"""Tests for fork_meter.models."""

from fork_meter.models import ComplexityResult


def _make(start: int = 1, end: int = 10, complexity: int = 3) -> ComplexityResult:
    return ComplexityResult(
        "foo.py", "Python", "function", "bar", None, start, end, complexity
    )


def test_fields_round_trip():
    res = ComplexityResult(
        file_path="src/main.py",
        language="Python",
        fragment_type="method",
        name="run",
        parent_class="App",
        start_line=5,
        end_line=20,
        complexity=7,
    )
    assert res.file_path == "src/main.py"
    assert res.language == "Python"
    assert res.fragment_type == "method"
    assert res.name == "run"
    assert res.parent_class == "App"
    assert res.start_line == 5
    assert res.end_line == 20
    assert res.complexity == 7


def test_parent_class_none():
    res = _make()
    assert res.parent_class is None


def test_line_count_multi_line():
    res = _make(start=5, end=15)
    assert res.line_count == 11


def test_line_count_single_line():
    res = _make(start=7, end=7)
    assert res.line_count == 1


def test_dataclass_equality():
    res1 = _make()
    res2 = _make()
    assert res1 == res2


def test_dataclass_inequality():
    assert _make(complexity=3) != _make(complexity=4)
