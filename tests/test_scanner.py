"""Tests for fork_meter.scanner."""

from braincraft import IgnoreFile

from fork_meter.scanner import EXTENSION_TO_LANGUAGE, _DEFAULT_EXCLUDE_DIRS, scan


def test_extension_mapping_python():
    assert EXTENSION_TO_LANGUAGE[".py"] == "Python"


def test_extension_mapping_javascript():
    assert EXTENSION_TO_LANGUAGE[".js"] == "JavaScript"
    assert EXTENSION_TO_LANGUAGE[".mjs"] == "JavaScript"
    assert EXTENSION_TO_LANGUAGE[".cjs"] == "JavaScript"


def test_extension_mapping_typescript():
    assert EXTENSION_TO_LANGUAGE[".ts"] == "TypeScript"
    assert EXTENSION_TO_LANGUAGE[".tsx"] == "TypeScript"


def test_extension_mapping_java():
    assert EXTENSION_TO_LANGUAGE[".java"] == "Java"


def test_extension_mapping_go():
    assert EXTENSION_TO_LANGUAGE[".go"] == "Go"


def test_extension_mapping_gosu():
    assert EXTENSION_TO_LANGUAGE[".gs"] == "Gosu"
    assert EXTENSION_TO_LANGUAGE[".gsx"] == "Gosu"


def test_extension_mapping_c():
    assert EXTENSION_TO_LANGUAGE[".c"] == "C"


def test_extension_mapping_cpp():
    assert EXTENSION_TO_LANGUAGE[".cpp"] == "C++"
    assert EXTENSION_TO_LANGUAGE[".cc"] == "C++"
    assert EXTENSION_TO_LANGUAGE[".cxx"] == "C++"
    assert EXTENSION_TO_LANGUAGE[".c++"] == "C++"


def test_extension_mapping_csharp():
    assert EXTENSION_TO_LANGUAGE[".cs"] == "C#"


def test_extension_mapping_rust():
    assert EXTENSION_TO_LANGUAGE[".rs"] == "Rust"


def test_extension_mapping_kotlin():
    assert EXTENSION_TO_LANGUAGE[".kt"] == "Kotlin"
    assert EXTENSION_TO_LANGUAGE[".kts"] == "Kotlin"


def test_extension_mapping_scala():
    assert EXTENSION_TO_LANGUAGE[".scala"] == "Scala"
    assert EXTENSION_TO_LANGUAGE[".sc"] == "Scala"


def test_header_extensions_not_mapped():
    assert ".h" not in EXTENSION_TO_LANGUAGE
    assert ".hpp" not in EXTENSION_TO_LANGUAGE


def test_default_exclude_dirs_contains_venv():
    assert ".venv" in _DEFAULT_EXCLUDE_DIRS
    assert "__pycache__" in _DEFAULT_EXCLUDE_DIRS
    assert "node_modules" in _DEFAULT_EXCLUDE_DIRS


def test_scan_finds_python_file(tmp_path):
    (tmp_path / "foo.py").write_text("x = 1")
    result = scan((tmp_path,))
    assert any(p.name == "foo.py" and lang == "Python" for p, lang in result)


def test_scan_ignores_unsupported_extension(tmp_path):
    (tmp_path / "notes.txt").write_text("hello")
    result = scan((tmp_path,))
    assert result == []


def test_scan_skips_default_excluded_dirs(tmp_path):
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "helper.py").write_text("x = 1")
    result = scan((tmp_path,))
    assert result == []


def test_scan_applies_exclude_patterns(tmp_path):
    (tmp_path / "keep.py").write_text("x = 1")
    (tmp_path / "skip.py").write_text("y = 2")
    result = scan((tmp_path,), exclude_patterns=("*/skip.py",))
    names = [p.name for p, _ in result]
    assert "keep.py" in names
    assert "skip.py" not in names


def test_scan_deduplicates_paths(tmp_path):
    f = tmp_path / "foo.py"
    f.write_text("x = 1")
    result = scan((tmp_path, f))
    assert [p for p, _ in result].count(f.resolve()) == 1


def test_scan_single_file_directly(tmp_path):
    f = tmp_path / "main.go"
    f.write_text("package main")
    result = scan((f,))
    assert len(result) == 1
    assert result[0][1] == "Go"


def test_scan_multiple_languages(tmp_path):
    (tmp_path / "app.py").write_text("x = 1")
    (tmp_path / "app.js").write_text("var x = 1;")
    result = scan((tmp_path,))
    langs = {lang for _, lang in result}
    assert langs == {"Python", "JavaScript"}


def test_scan_applies_ignore_file(tmp_path):
    (tmp_path / "keep.py").write_text("x = 1")
    (tmp_path / "skip.py").write_text("y = 2")
    ignore_path = tmp_path / ".fm_ignore"
    ignore_path.write_text("skip.py\n")
    ignore_file = IgnoreFile(ignore_path, base_dir=tmp_path)
    result = scan((tmp_path,), ignore_file=ignore_file)
    names = [p.name for p, _ in result]
    assert "keep.py" in names
    assert "skip.py" not in names


def test_scan_ignore_file_applies_to_directories(tmp_path):
    ignored_dir = tmp_path / "legacy"
    ignored_dir.mkdir()
    (ignored_dir / "old.py").write_text("x = 1")
    (tmp_path / "new.py").write_text("x = 1")
    ignore_path = tmp_path / ".fm_ignore"
    ignore_path.write_text("legacy/\n")
    ignore_file = IgnoreFile(ignore_path, base_dir=tmp_path)
    result = scan((tmp_path,), ignore_file=ignore_file)
    names = [p.name for p, _ in result]
    assert "new.py" in names
    assert "old.py" not in names
