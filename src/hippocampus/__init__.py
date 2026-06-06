"""Migration shim for the pre-rename ``hippocampus`` package."""

from __future__ import annotations

import warnings

import hippos as _hippos

__version__ = _hippos.__version__
__all__ = list(_hippos.__all__)

warnings.warn(
    "The 'hippocampus' package name is deprecated; use 'hippos' instead.",
    DeprecationWarning,
    stacklevel=2,
)


def __getattr__(name: str):
    return getattr(_hippos, name)
