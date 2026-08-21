"""Tests for fork_meter.parser."""

from fork_meter import parser as _parser


def test_get_language_python():
    lang = _parser.get_language("Python")
    assert lang is not None


def test_get_language_javascript():
    assert _parser.get_language("JavaScript") is not None


def test_get_language_typescript():
    assert _parser.get_language("TypeScript") is not None


def test_get_language_java():
    assert _parser.get_language("Java") is not None


def test_get_language_go():
    assert _parser.get_language("Go") is not None


def test_get_language_gosu():
    assert _parser.get_language("Gosu") is not None


def test_get_language_unknown():
    assert _parser.get_language("COBOL") is None


def test_parse_python_returns_tree():
    tree = _parser.parse(b"x = 1\n", "Python")
    assert tree is not None
    assert not tree.root_node.has_error


def test_parse_unknown_language_returns_none():
    tree = _parser.parse(b"x = 1", "COBOL")
    assert tree is None


def test_parse_invalid_syntax_still_returns_tree():
    # tree-sitter is error-tolerant and always returns a tree.
    tree = _parser.parse(b"def (broken:", "Python")
    assert tree is not None
