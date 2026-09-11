"""
Entry point for the fork-meter command-line tool.

:author: Ron Webb
:since: 1.0.0
"""

import logging
import sys
import time
from pathlib import Path

import click
from braincraft import IgnoreFile
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

from . import CONF_DIR, IGNORE_FILE, __version__
from .analyzer import analyze
from .config import Config
from .reporter import html_reporter, json_reporter

_logger = logging.getLogger(__name__)
_config = Config()


def _ensure_utf8_streams() -> None:
    """Reconfigure stdout/stderr to UTF-8 so redirected/piped output never raises UnicodeEncodeError."""
    for stream in (sys.stdout, sys.stderr):
        encoding: str = str(getattr(stream, "encoding", None) or "")
        if hasattr(stream, "reconfigure") and encoding.lower() != "utf-8":
            stream.reconfigure(encoding="utf-8", errors="replace")


_ensure_utf8_streams()
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


def _load_ignore_file() -> IgnoreFile | None:
    """Return the configured :class:`~braincraft.IgnoreFile`, falling back to the bundled default."""
    ignore_path = Path(CONF_DIR) / _config.get_ignore_file()
    _logger.debug("Loading ignore file from: %s", ignore_path)
    try:
        return IgnoreFile(ignore_path)
    except FileNotFoundError as exc:
        if ignore_path == Path(IGNORE_FILE):
            _logger.warning("Ignore file unavailable: %s", exc)
            return None
        _logger.warning(
            "Configured ignore file unavailable (%s); falling back to default.", exc
        )
    try:
        return IgnoreFile(Path(IGNORE_FILE))
    except FileNotFoundError as exc:
        _logger.warning("Ignore file unavailable: %s", exc)
        return None


def _read_target_list(list_file: Path) -> list[Path]:
    """Read one target path per line from *list_file*, skipping blanks and ``#`` comments."""
    result: list[Path] = []
    for line in list_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            result.append(Path(stripped))
    return result


def _build_progress() -> Progress:
    """Return a transient :class:`~rich.progress.Progress` for the file-checking status."""
    return Progress(
        TextColumn("[bold cyan]fork-meter[/bold cyan] checking files"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=_console,
        transient=True,
    )


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
@click.option(
    "--target-list",
    "target_list",
    is_flag=True,
    default=False,
    help=(
        "Treat PATHS as a single existing file listing target paths (files "
        "and/or directories), one per line, instead of separate arguments. "
        "Blank lines and lines starting with '#' are skipped."
    ),
)
@click.version_option(
    version=__version__, prog_name="fork-meter", message="%(prog)s v%(version)s"
)
def main(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    paths: tuple[str, ...],
    max_threshold: int,
    output_name: str,
    output_dir: str | None,
    output_format: str,
    exclude: tuple[str, ...],
    target_list: bool,
) -> None:
    """Measure cyclomatic complexity of source code.

    PATH arguments may be files or directories; directories are scanned recursively.
    Only functions with complexity strictly above --max are included in the report.
    With --target-list, PATHS must be a single file listing targets, one per line.
    """
    _logger.info("fork-meter started")

    if target_list:
        if len(paths) != 1 or not Path(paths[0]).is_file():
            raise click.UsageError(
                "--target-list requires PATHS to be a single existing file."
            )
        resolved_paths = tuple(_read_target_list(Path(paths[0])))
    else:
        resolved_paths = tuple(Path(p) for p in paths)
    out_dir = Path(output_dir) if output_dir else Path.cwd() / "reports"

    start = time.monotonic()
    with _build_progress() as progress:
        task = progress.add_task("checking", total=None)
        result = analyze(
            resolved_paths,
            exclude_patterns=exclude,
            max_threshold=max_threshold,
            ignore_file=_load_ignore_file(),
            on_progress=lambda done, total: progress.update(
                task, completed=done, total=total
            ),
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

    if result.results:
        sys.exit(1)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
