"""Fallback data builders used when the external repomix CLI is unavailable."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..source_filter import build_file_manifest


def _safe_relative_path(value: object) -> Path | None:
    if not isinstance(value, str):
        return None
    rel_path = Path(value)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        return None
    if not rel_path.parts:
        return None
    return rel_path


def read_manifest_source_files(
    target: Path,
    file_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = file_manifest if file_manifest is not None else build_file_manifest(target)
    manifest_files = manifest.get("files", {})
    files: dict[str, str] = {}
    if not isinstance(manifest_files, dict):
        return {"files": files}

    for rel, metadata in sorted(manifest_files.items()):
        rel_path = _safe_relative_path(rel)
        if rel_path is None or not isinstance(metadata, dict):
            continue
        if not metadata.get("include_in_architecture"):
            continue

        try:
            files[str(rel)] = (target / rel_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return {"files": files}


def build_directory_structure(
    target: Path,
    file_manifest: dict[str, Any] | None = None,
) -> dict[str, str]:
    manifest = file_manifest if file_manifest is not None else build_file_manifest(target)
    manifest_files = manifest.get("files", {})
    tree: dict[str, Any] = {}
    if not isinstance(manifest_files, dict):
        return {"directoryStructure": ""}

    for rel in sorted(manifest_files):
        rel_path = _safe_relative_path(rel)
        if rel_path is None:
            continue
        node = tree
        for part in rel_path.parts[:-1]:
            node = node.setdefault(part, {})
        node.setdefault(rel_path.parts[-1], None)

    lines: list[str] = []

    def walk(node: dict[str, Any], depth: int) -> None:
        dirs = sorted(name for name, child in node.items() if isinstance(child, dict))
        files = sorted(name for name, child in node.items() if not isinstance(child, dict))
        for name in dirs:
            lines.append(f"{'  ' * depth}{name}/")
            walk(node[name], depth + 1)
        for name in files:
            lines.append(f"{'  ' * depth}{name}")

    walk(tree, 0)
    return {"directoryStructure": "\n".join(lines)}
