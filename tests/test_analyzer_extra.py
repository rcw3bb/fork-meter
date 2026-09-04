"""Tests for fork_meter.analyzer — additional coverage for edge cases."""

import pytest
from braincraft import IgnoreFile

from fork_meter.analyzer import _get_parent_class_go, analyze, analyze_file
from fork_meter import parser as _parser


def test_analyze_file_unknown_language_returns_empty(tmp_path):
    f = tmp_path / "test.py"
    f.write_bytes(b"def foo():\n    pass\n")
    # "COBOL" has no grammar, so parse() returns None.
    assert analyze_file(f, "COBOL") == []


def test_go_function_no_parent_class(tmp_path):
    src = b"""package main

func add(a int, b int) int {
\tif a > 0 {
\t\treturn a + b
\t}
\treturn b
}
"""
    f = tmp_path / "main.go"
    f.write_bytes(src)
    results = analyze_file(f, "Go")
    assert len(results) == 1
    res = results[0]
    assert res.name == "add"
    assert res.parent_class is None
    assert res.fragment_type == "function"
    assert res.complexity == 2  # 1 base + 1 if


def test_go_method_extracts_receiver_type(tmp_path):
    src = b"""package main

type Counter struct{ val int }

func (c *Counter) Increment(delta int) {
\tfor i := 0; i < delta; i++ {
\t\tc.val++
\t}
}
"""
    f = tmp_path / "counter.go"
    f.write_bytes(src)
    results = analyze_file(f, "Go")
    assert len(results) == 1
    res = results[0]
    assert res.name == "Increment"
    assert res.parent_class == "Counter"
    assert res.fragment_type == "method"
    assert res.complexity == 2  # 1 base + 1 for


def test_java_method_complexity(tmp_path):
    src = b"""public class Calc {
    public int compute(int x) {
        if (x > 0) {
            for (int i = 0; i < x; i++) {
                if (i % 2 == 0) {
                    x--;
                }
            }
        }
        return x;
    }
}
"""
    f = tmp_path / "Calc.java"
    f.write_bytes(src)
    results = analyze_file(f, "Java")
    assert len(results) == 1
    res = results[0]
    assert res.name == "compute"
    assert res.parent_class == "Calc"
    assert res.fragment_type == "method"
    assert res.complexity >= 3  # 1 base + at least 2 decision points


def test_javascript_function_complexity(tmp_path):
    src = b"""function process(items) {
    for (let i = 0; i < items.length; i++) {
        if (items[i] > 0) {
            items[i]++;
        }
    }
    return items;
}
"""
    f = tmp_path / "app.js"
    f.write_bytes(src)
    results = analyze_file(f, "JavaScript")
    assert any(r.name == "process" for r in results)
    process = next(r for r in results if r.name == "process")
    assert process.complexity >= 3  # 1 base + for + if


def test_python_ternary_expression(tmp_path):
    src = b"""def sign(x):
    return 1 if x > 0 else -1
"""
    f = tmp_path / "sign.py"
    f.write_bytes(src)
    results = analyze_file(f, "Python")
    assert len(results) == 1
    assert results[0].complexity == 2  # 1 base + 1 conditional_expression


def test_get_parent_class_go_no_receiver():
    # Call with a fake node-like object that lacks a receiver field.
    class FakeNode:
        def child_by_field_name(self, _name):
            return None

    assert _get_parent_class_go(FakeNode()) is None


def test_analyze_forwards_ignore_file(tmp_path):
    (tmp_path / "keep.py").write_bytes(b"def foo():\n    if True:\n        pass\n")
    (tmp_path / "skip.py").write_bytes(b"def bar():\n    if True:\n        pass\n")
    ignore_path = tmp_path / ".fm_ignore"
    ignore_path.write_text("skip.py\n")
    ignore_file = IgnoreFile(ignore_path, base_dir=tmp_path)
    result = analyze((tmp_path,), max_threshold=0, ignore_file=ignore_file)
    names = {r.name for r in result.results}
    assert "foo" in names
    assert "bar" not in names
