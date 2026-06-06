from __future__ import annotations

import os
from pathlib import Path


HIPPOS_LLM_CONFIG_NAME = "config.yaml"


def user_config_dir() -> Path:
    override = str(os.environ.get("HIPPOS_USER_CONFIG_DIR", "") or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    legacy_override = str(os.environ.get("HIPPOCAMPUS_USER_CONFIG_DIR", "") or "").strip()
    if legacy_override:
        return Path(legacy_override).expanduser().resolve()
    legacy_dir = (Path.home() / ".hippocampus").resolve()
    if legacy_dir.exists() and not (Path.home() / ".hippos").exists():
        return legacy_dir
    return (Path.home() / ".hippos").resolve()


def project_state_dir(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / ".hippos"


def legacy_project_state_dir(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / ".hippocampus"


def resolve_hippos_llm_config_file(project_root: str | Path | None = None) -> Path:
    if project_root is not None:
        local_override = project_state_dir(project_root) / HIPPOS_LLM_CONFIG_NAME
        if local_override.exists():
            return local_override
        legacy_override = legacy_project_state_dir(project_root) / HIPPOS_LLM_CONFIG_NAME
        if legacy_override.exists():
            return legacy_override
    return user_config_dir() / HIPPOS_LLM_CONFIG_NAME


# Migration aliases for callers moving from the old names.
HIPPOCAMPUS_LLM_CONFIG_NAME = HIPPOS_LLM_CONFIG_NAME
resolve_hippo_llm_config_file = resolve_hippos_llm_config_file


__all__ = [
    "HIPPOS_LLM_CONFIG_NAME",
    "legacy_project_state_dir",
    "project_state_dir",
    "resolve_hippo_llm_config_file",
    "resolve_hippos_llm_config_file",
    "user_config_dir",
]
