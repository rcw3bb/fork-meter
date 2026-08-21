"""
Entry point for the fork-meter command-line tool.

:author: Ron Webb
:since: 1.0.0
"""

import logging
import time
from pathlib import Path

import click
from rich.console import Console

from . import __version__
from .analyzer import analyze
from .reporter import html_reporter, json_reporter

_logger = logging.getLogger(__name__)
_console = Console()

_CC_STYLE = {
    (1, 5): "green",
    (6, 10): "yellow",
    (11, 15): "orange3",
    (16, 9999): "red",
}


def _print_elapsed(elapsed: float, written: list[Path]) -> None:
    """Print a single-line elapsed status with report paths."""
    _console.print(
        f"[bold cyan]fork-meter[/bold cyan] done in [bold]{elapsed:.2f}s[/bold]"
    )
    for path in written:
        _console.print(f"  [green]\u2713[/green] {path}")


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--max",
    "max_threshold",
    default=10,
    show_default=True,
    metavar="INT",
    help="Report functions with complexity strictly above this value.",
)
@click.option(
    "--output",
    "output_name",
    default="fork-meter-output",
    show_default=True,
    metavar="NAME",
    help="Base name for output files (no extension).",
)
@click.option(
    "--output-dir",
    default=None,
    type=click.Path(),
    metavar="DIR",
    help="Directory for output files. Defaults to <cwd>/reports.",
)
@click.option(
    "--format",
    "output_format",
    default="both",
    type=click.Choice(["json", "html", "both"], case_sensitive=False),
    show_default=True,
    help="Output format.",
)
@click.option(
    "--exclude",
    multiple=True,
    metavar="PATTERN",
    help="Glob pattern to exclude from scanning (repeatable).",
)
@click.version_option(version=__version__, prog_name="fork-meter")
def main(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    paths: tuple[str, ...],
    max_threshold: int,
    output_name: str,
    output_dir: str | None,
    output_format: str,
    exclude: tuple[str, ...],
) -> None:
    """Measure cyclomatic complexity of source code.

    PATH arguments may be files or directories; directories are scanned recursively.
    Only functions with complexity strictly above --max are included in the report.
    """
    _logger.info("fork-meter started")

    resolved_paths = tuple(Path(p) for p in paths)
    out_dir = Path(output_dir) if output_dir else Path.cwd() / "reports"

    start = time.monotonic()
    result = analyze(
        resolved_paths, exclude_patterns=exclude, max_threshold=max_threshold
    )

    written: list[Path] = []
    if output_format in ("json", "both"):
        written.append(
            json_reporter.write(
                result,
                [str(p) for p in resolved_paths],
                max_threshold,
                out_dir / f"{output_name}.json",
            )
        )
    if output_format in ("html", "both"):
        written.append(
            html_reporter.write(result, max_threshold, out_dir / f"{output_name}.html")
        )

    _print_elapsed(time.monotonic() - start, written)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
