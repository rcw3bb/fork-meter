"""
fork_meter package.

A command-line tool that measures cyclomatic complexity by counting
decision points and branching paths in source code.

:author: Ron Webb
:since: 1.0.0
"""

from env_dir_bootstrap import EnvDirBootstrap
from logenrich import setup_logger

__version__ = "1.1.1"

_bootstrapper = EnvDirBootstrap(
    env_var="FORK_METER_CONFIG_DIR",
    resources=["logging.ini", "fm_ignore"],
    package="fork_meter",
)

_bootstrapper.setup()

CONF_DIR = str(_bootstrapper.get_dir())
IGNORE_FILE = str(_bootstrapper.resolve("fm_ignore"))

setup_logger("fork_meter", conf_dir=CONF_DIR)
