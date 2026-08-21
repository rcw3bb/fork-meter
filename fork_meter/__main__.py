"""
Entry point for the fork-meter command-line tool.

:author: Ron Webb
:since: 1.0.0
"""

import logging

_logger = logging.getLogger(__name__)


def main() -> None:
    """Run the fork-meter CLI."""
    _logger.info("fork-meter started")


if __name__ == "__main__":
    main()
