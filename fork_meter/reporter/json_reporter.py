"""
JSON reporter for fork-meter complexity analysis.

:author: Ron Webb
:since: 1.0.0
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .. import __version__
from ..analyzer import AnalysisResult

_logger = logging.getLogger(__name__)


def write(
    result: AnalysisResult,
    scan_paths: list[str],
    max_threshold: int,
    output_path: Path,
) -> Path:
    """Write *result* to a JSON file at *output_path*.

    :param result: Aggregated analysis output.
    :param scan_paths: Original paths supplied by the user.
    :param max_threshold: Complexity threshold used for filtering.
    :param output_path: Destination ``.json`` file path.
    :returns: Resolved path of the written file.
    """
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "scan_paths": scan_paths,
        "max_threshold": max_threshold,
        "summary": {
            "files_scanned": result.files_scanned,
            "functions_analyzed": result.functions_analyzed,
            "above_threshold": len(result.results),
        },
        "results": [
            {
                "file_path": r.file_path,
                "language": r.language,
                "fragment_type": r.fragment_type,
                "name": r.name,
                "parent_class": r.parent_class,
                "start_line": r.start_line,
                "end_line": r.end_line,
                "complexity": r.complexity,
            }
            for r in result.results
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _logger.info("JSON report written to %s", output_path)
    return output_path.resolve()
