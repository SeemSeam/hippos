"""Path helpers for Hippos state and short-term legacy migration."""

from __future__ import annotations

from pathlib import Path

from .constants import (
    CONFIG_FILE,
    HIPPOS_DIR,
    INDEX_FILE,
    LEGACY_HIPPOS_DIR,
    LEGACY_INDEX_FILE,
)


def state_dir_for_write(project_root: str | Path) -> Path:
    """Return the canonical state directory for new Hippos output."""
    return Path(project_root).resolve() / HIPPOS_DIR


def legacy_state_dir(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / LEGACY_HIPPOS_DIR


def state_dir_for_read(project_root: str | Path) -> Path:
    """Return the existing state dir, preferring new Hippos state."""
    root = Path(project_root).resolve()
    current = root / HIPPOS_DIR
    if current.exists():
        return current
    legacy = root / LEGACY_HIPPOS_DIR
    if legacy.exists():
        return legacy
    return current


def index_file_for_read(output_dir: str | Path) -> Path:
    """Return the existing index path, preferring the new filename."""
    out = Path(output_dir).resolve()
    current = out / INDEX_FILE
    if current.exists():
        return current
    legacy = out / LEGACY_INDEX_FILE
    if legacy.exists():
        return legacy
    return current


def config_file_for_read(project_root: str | Path) -> Path:
    """Return the project config path, preferring new Hippos config."""
    root = Path(project_root).resolve()
    current = root / HIPPOS_DIR / CONFIG_FILE
    if current.exists():
        return current
    legacy = root / LEGACY_HIPPOS_DIR / CONFIG_FILE
    if legacy.exists():
        return legacy
    return current


__all__ = [
    "config_file_for_read",
    "index_file_for_read",
    "legacy_state_dir",
    "state_dir_for_read",
    "state_dir_for_write",
]
