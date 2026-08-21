"""Tests for fork_meter.analyzer."""

from fork_meter.analyzer import AnalysisResult, analyze, analyze_file


def test_simple_function_complexity_one(tmp_path):
    f = tmp_path / "test.py"
    f.write_bytes(b"def greet(name):\n    return 'Hello ' + name\n")
    results = analyze_file(f, "Python")
    assert len(results) == 1
    assert results[0].name == "greet"
    assert results[0].complexity == 1
    assert results[0].fragment_type == "function"
    assert results[0].parent_class is None


def test_if_increments_complexity(tmp_path):
    f = tmp_path / "test.py"
    f.write_bytes(b"def foo(x):\n    if x > 0:\n        return x\n    return -x\n")
    results = analyze_file(f, "Python")
    assert len(results) == 1
    assert results[0].complexity == 2  # 1 base + 1 if


def test_elif_increments_complexity(tmp_path):
    src = b"""
def classify(n):
    if n < 0:
        return "neg"
    elif n == 0:
        return "zero"
    elif n < 10:
        return "small"
    else:
        return "large"
"""
    f = tmp_path / "test.py"
    f.write_bytes(src)
    results = analyze_file(f, "Python")
    assert len(results) == 1
    assert results[0].complexity == 4  # 1 base + 1 if + 2 elif


def test_for_and_if_combined(tmp_path):
    src = b"""
def bar(items):
    for item in items:
        if item > 0:
            pass
"""
    f = tmp_path / "test.py"
    f.write_bytes(src)
    results = analyze_file(f, "Python")
    assert len(results) == 1
    assert results[0].complexity == 3  # 1 base + 1 for + 1 if


def test_except_clauses(tmp_path):
    src = b"""
def safe(x):
    try:
        return int(x)
    except ValueError:
        return 0
    except TypeError:
        return -1
"""
    f = tmp_path / "test.py"
    f.write_bytes(src)
    results = analyze_file(f, "Python")
    assert len(results) == 1
    assert results[0].complexity == 3  # 1 base + 2 except


def test_method_detects_parent_class(tmp_path):
    src = b"""
class Foo:
    def bar(self, x):
        for i in range(x):
            if i % 2 == 0:
                pass
"""
    f = tmp_path / "test.py"
    f.write_bytes(src)
    results = analyze_file(f, "Python")
    assert len(results) == 1
    res = results[0]
    assert res.name == "bar"
    assert res.parent_class == "Foo"
    assert res.fragment_type == "method"
    assert res.complexity == 3  # 1 base + 1 for + 1 if


def test_nested_function_pruned_from_outer(tmp_path):
    src = b"""
def outer(x):
    if x > 0:
        def inner(y):
            if y > 0:
                if y > 10:
                    return y
        return inner
    return None
"""
    f = tmp_path / "test.py"
    f.write_bytes(src)
    results = analyze_file(f, "Python")
    outer = next(r for r in results if r.name == "outer")
    inner = next(r for r in results if r.name == "inner")
    assert outer.complexity == 2  # 1 base + 1 outer-if (inner pruned)
    assert inner.complexity == 3  # 1 base + 2 inner-ifs


def test_no_code_blocks_returns_empty(tmp_path):
    f = tmp_path / "test.py"
    f.write_bytes(b"CONSTANT = 42\n")
    assert analyze_file(f, "Python") == []


def test_unreadable_file_returns_empty(tmp_path):
    missing = tmp_path / "ghost.py"
    assert analyze_file(missing, "Python") == []


def test_analyze_filters_by_threshold(tmp_path):
    src = b"""
def simple(x):
    return x

def complex_func(x):
    if x > 0:
        if x > 10:
            if x > 100:
                if x > 1000:
                    if x > 10000:
                        if x > 100000:
                            if x > 1000000:
                                if x > 10000000:
                                    if x > 100000000:
                                        if x > 1000000000:
                                            return "huge"
    return 0
"""
    f = tmp_path / "test.py"
    f.write_bytes(src)
    result = analyze((tmp_path,), max_threshold=10)
    assert isinstance(result, AnalysisResult)
    assert result.files_scanned == 1
    assert result.functions_analyzed == 2
    assert len(result.results) == 1
    assert result.results[0].name == "complex_func"
    assert result.results[0].complexity > 10


def test_analyze_empty_directory(tmp_path):
    result = analyze((tmp_path,), max_threshold=10)
    assert result.files_scanned == 0
    assert result.functions_analyzed == 0
    assert result.results == []


def test_analyze_exclude_pattern(tmp_path):
    (tmp_path / "keep.py").write_bytes(b"def foo():\n    if True:\n        pass\n")
    (tmp_path / "skip.py").write_bytes(b"def bar():\n    if True:\n        pass\n")
    result = analyze((tmp_path,), exclude_patterns=("*/skip.py",), max_threshold=0)
    names = {r.name for r in result.results}
    assert "foo" in names
    assert "bar" not in names


def test_line_count_in_result(tmp_path):
    src = b"def foo():\n    x = 1\n    return x\n"
    f = tmp_path / "test.py"
    f.write_bytes(src)
    results = analyze_file(f, "Python")
    assert len(results) == 1
    assert results[0].line_count >= 1
    assert results[0].start_line <= results[0].end_line
