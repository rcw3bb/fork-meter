"""
Cyclomatic complexity analyzer using tree-sitter AST traversal.

:author: Ron Webb
:since: 1.0.0
"""

import logging
from bisect import bisect_left
from dataclasses import dataclass, field
from pathlib import Path

from tree_sitter import Language, Node, Query, QueryCursor

from . import parser as _parser
from . import scanner as _scanner
from .models import ComplexityResult

_logger = logging.getLogger(__name__)

# Per-language S-expression queries selecting named functions, methods, and constructors.
_FRAGMENT_QUERIES: dict[str, str] = {
    "Python": "(function_definition) @fragment",
    "JavaScript": "[(function_declaration) (method_definition)] @fragment",
    "TypeScript": "[(function_declaration) (method_definition)] @fragment",
    "Java": "[(method_declaration) (constructor_declaration)] @fragment",
    "Go": "[(function_declaration) (method_declaration)] @fragment",
    "Gosu": "[(function_declaration) (constructor_declaration)] @fragment",
}

# Node types that represent a branching decision point per language.
_DECISION_NODES: dict[str, frozenset[str]] = {
    "Python": frozenset(
        {
            "if_statement",
            "elif_clause",
            "for_statement",
            "while_statement",
            "except_clause",
            "conditional_expression",
            "case_clause",
        }
    ),
    "JavaScript": frozenset(
        {
            "if_statement",
            "for_statement",
            "for_in_statement",
            "for_of_statement",
            "while_statement",
            "do_statement",
            "catch_clause",
            "switch_case",
            "ternary_expression",
        }
    ),
    "TypeScript": frozenset(
        {
            "if_statement",
            "for_statement",
            "for_in_statement",
            "for_of_statement",
            "while_statement",
            "do_statement",
            "catch_clause",
            "switch_case",
            "ternary_expression",
        }
    ),
    "Java": frozenset(
        {
            "if_statement",
            "for_statement",
            "enhanced_for_statement",
            "while_statement",
            "do_statement",
            "catch_clause",
            "switch_label",
            "ternary_expression",
        }
    ),
    "Go": frozenset({"if_statement", "for_statement", "case_clause", "comm_clause"}),
    "Gosu": frozenset(
        {
            "if_statement",
            "for_statement",
            "while_statement",
            "do_while_statement",
            "catch_clause",
            "switch_label",
            "ternary_expression",
        }
    ),
}

# Node types whose subtrees are pruned during decision-point counting (nested code units).
_NESTED_STOP_TYPES: dict[str, frozenset[str]] = {
    "Python": frozenset({"function_definition", "class_definition"}),
    "JavaScript": frozenset(
        {
            "function_declaration",
            "function_expression",
            "arrow_function",
            "method_definition",
            "class_declaration",
        }
    ),
    "TypeScript": frozenset(
        {
            "function_declaration",
            "function_expression",
            "arrow_function",
            "method_definition",
            "class_declaration",
        }
    ),
    "Java": frozenset(
        {
            "method_declaration",
            "constructor_declaration",
            "class_declaration",
            "lambda_expression",
        }
    ),
    "Go": frozenset({"function_declaration", "method_declaration", "func_literal"}),
    "Gosu": frozenset(
        {"function_declaration", "constructor_declaration", "class_declaration"}
    ),
}

# AST node types that represent a class body, used when walking up the parent chain.
_CLASS_NODE_TYPES: frozenset[str] = frozenset(
    {
        "class_definition",  # Python
        "class_declaration",  # JavaScript, TypeScript, Java, Gosu
    }
)

_FRAGMENT_TYPE_MAP: dict[str, str] = {
    "function_definition": "function",
    "function_declaration": "function",
    "method_definition": "method",
    "method_declaration": "method",
    "constructor_declaration": "constructor",
}


@dataclass
class AnalysisResult:
    """Aggregated output of a complexity analysis run.

    :param files_scanned: Number of source files processed.
    :param functions_analyzed: Total named code blocks measured before threshold filtering.
    :param results: Complexity results with ``complexity > max_threshold``.
    """

    files_scanned: int
    functions_analyzed: int
    results: list[ComplexityResult] = field(default_factory=list)


def _get_name(node: Node) -> str | None:
    """Return the declared name of *node*, or ``None`` for anonymous code blocks."""
    name_node = node.child_by_field_name("name")
    if name_node is None:
        return None
    return name_node.text.decode("utf-8", errors="replace")


def _get_parent_class_go(node: Node) -> str | None:
    """Return the receiver type name for a Go ``method_declaration``."""
    receiver = node.child_by_field_name("receiver")
    if receiver is None:
        return None
    for child in receiver.children:
        if child.type == "parameter_declaration":
            type_node = child.child_by_field_name("type")
            if type_node is None:
                continue
            if type_node.type == "pointer_type":
                # *Foo — get the named inner type (skip the '*' token)
                for inner in reversed(type_node.children):
                    if inner.is_named:
                        return inner.text.decode("utf-8", errors="replace")
            return type_node.text.decode("utf-8", errors="replace")
    return None


def _get_parent_class(node: Node, language: str) -> str | None:
    """Return the enclosing class name, or ``None`` for top-level code blocks."""
    if language == "Go" and node.type == "method_declaration":
        return _get_parent_class_go(node)
    current = node.parent
    while current is not None:
        if current.type in _CLASS_NODE_TYPES:
            name_node = current.child_by_field_name("name")
            if name_node is not None:
                return name_node.text.decode("utf-8", errors="replace")
        current = current.parent
    return None


def _resolve_fragment_type(node: Node, language: str, parent_class: str | None) -> str:
    """Return the fragment type string for *node*."""
    raw = _FRAGMENT_TYPE_MAP.get(node.type, "function")
    # Python uses function_definition for both functions and methods.
    if (
        language == "Python"
        and node.type == "function_definition"
        and parent_class is not None
    ):
        return "method"
    return raw


def _count_decisions(
    node: Node, decision_nodes: frozenset[str], stop_types: frozenset[str]
) -> int:
    """Recursively count decision-point nodes under *node*, pruning at *stop_types*.

    :param node: AST node to walk (typically the function/method root).
    :param decision_nodes: Node type names that each add one to the complexity count.
    :param stop_types: Node types whose entire subtrees are excluded (nested code units).
    :returns: Total decision points found within *node*'s subtree.
    """
    count = 0
    for child in node.children:
        if child.type in stop_types:
            continue
        if child.type in decision_nodes:
            count += 1
        count += _count_decisions(child, decision_nodes, stop_types)
    return count


def _compile_query(lang: Language, pattern: str, language_name: str) -> Query | None:
    """Return a compiled tree-sitter Query, or ``None`` on failure."""
    try:
        return Query(lang, pattern)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        _logger.warning("Failed to compile query for %s: %s", language_name, exc)
        return None


def _capture_fragments(tree, language: str) -> list[Node]:
    """Run the fragment query for *language* against *tree* and return matched nodes."""
    lang_obj = _parser.get_language(language)
    if lang_obj is None:
        return []
    query_str = _FRAGMENT_QUERIES.get(language)
    if query_str is None:
        return []
    query = _compile_query(lang_obj, query_str, language)
    if query is None:
        return []
    cursor = QueryCursor(query)
    captures = cursor.captures(tree.root_node)
    nodes: list[Node] = list(captures.get("fragment", []))
    del cursor, captures
    return nodes


def _build_result(
    node: Node,
    file_path: str,
    language: str,
    newline_offsets: list[int],
) -> ComplexityResult | None:
    """Return a :class:`~fork_meter.models.ComplexityResult` for *node*, or ``None`` if anonymous."""
    name = _get_name(node)
    if name is None:
        return None
    parent_class = _get_parent_class(node, language)
    fragment_type = _resolve_fragment_type(node, language, parent_class)
    decision_nodes = _DECISION_NODES.get(language, frozenset())
    stop_types = _NESTED_STOP_TYPES.get(language, frozenset())
    complexity = 1 + _count_decisions(node, decision_nodes, stop_types)
    return ComplexityResult(
        file_path=file_path,
        language=language,
        fragment_type=fragment_type,
        name=name,
        parent_class=parent_class,
        start_line=bisect_left(newline_offsets, node.start_byte) + 1,
        end_line=bisect_left(newline_offsets, node.end_byte) + 1,
        complexity=complexity,
    )


def analyze_file(file_path: Path, language: str) -> list[ComplexityResult]:
    """Parse *file_path* and return a complexity result for each named code block.

    :param file_path: Path to a source file.
    :param language: Language name matching :data:`fork_meter.scanner.EXTENSION_TO_LANGUAGE`.
    :returns: Unsorted list of :class:`~fork_meter.models.ComplexityResult` objects.
    """
    try:
        source_bytes = file_path.read_bytes()
    except OSError as exc:
        _logger.warning("Cannot read %s: %s", file_path, exc)
        return []

    tree = _parser.parse(source_bytes, language)
    if tree is None:
        return []

    # Keep `tree` alive for the duration of node traversal; nodes reference its C memory.
    fragment_nodes = _capture_fragments(tree, language)
    newline_offsets = [i for i, b in enumerate(source_bytes) if b == ord(b"\n")]

    results: list[ComplexityResult] = []
    for node in fragment_nodes:
        built = _build_result(node, str(file_path), language, newline_offsets)
        if built is not None:
            results.append(built)

    _logger.debug("Analyzed %d code blocks in %s", len(results), file_path.name)
    return results


def analyze(
    paths: tuple[Path, ...],
    exclude_patterns: tuple[str, ...] = (),
    max_threshold: int = 10,
) -> AnalysisResult:
    """Scan *paths*, compute cyclomatic complexity, and filter results by threshold.

    :param paths: File or directory paths to scan.
    :param exclude_patterns: Glob patterns to exclude from scanning.
    :param max_threshold: Only include results with complexity strictly above this value.
    :returns: :class:`AnalysisResult` with summary counts and filtered results.
    """
    files = _scanner.scan(paths, exclude_patterns)
    all_results: list[ComplexityResult] = []
    for file_path, language in files:
        all_results.extend(analyze_file(file_path, language))

    filtered = [r for r in all_results if r.complexity > max_threshold]
    _logger.info(
        "Files: %d | Functions: %d | Above threshold: %d",
        len(files),
        len(all_results),
        len(filtered),
    )
    return AnalysisResult(
        files_scanned=len(files),
        functions_analyzed=len(all_results),
        results=filtered,
    )
