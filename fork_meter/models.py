"""
Data models for fork-meter cyclomatic complexity analysis.

:author: Ron Webb
:since: 1.0.0
"""

from dataclasses import dataclass


@dataclass
class ComplexityResult:  # pylint: disable=too-many-instance-attributes
    """Cyclomatic complexity measurement for a single named code block.

    :param file_path: Absolute path to the source file.
    :param language: Language name (e.g. ``"Python"``).
    :param fragment_type: Code block kind: ``"function"``, ``"method"``, or ``"constructor"``.
    :param name: Declared name of the code block.
    :param parent_class: Enclosing class name, or ``None`` for top-level functions.
    :param start_line: 1-based line where the code block starts.
    :param end_line: 1-based line where the code block ends.
    :param complexity: Cyclomatic complexity (≥ 1).
    """

    file_path: str
    language: str
    fragment_type: str
    name: str
    parent_class: str | None
    start_line: int
    end_line: int
    complexity: int

    @property
    def line_count(self) -> int:
        """Return the number of source lines spanned by this code block."""
        return self.end_line - self.start_line + 1
