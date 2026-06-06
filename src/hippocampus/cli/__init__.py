"""Migration shim for ``hippocampus.cli``."""

from __future__ import annotations

import warnings

from hippos.cli import *  # noqa: F401,F403
from hippos.cli import cli

warnings.warn(
    "'hippocampus.cli' is deprecated; use 'hippos.cli' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["cli"]
