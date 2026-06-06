"""Hippos - code repository indexing and analysis toolkit."""

from __future__ import annotations

__version__ = "0.1.7"

_API_EXPORTS = {
    "build_index",
    "build_tree",
    "build_tree_diff",
    "extract_file_definitions",
    "extract_signatures",
    "generate_structure_prompt",
    "infer_parent_definition",
    "initialize_project",
    "is_hidden_path",
    "language_for_file",
    "navigate",
    "navigate_context_pack",
    "render_context_snippets",
    "render_deduplicated_overview",
    "resolve_queries_dir",
    "summarize_project_index",
    "summarize_project_report",
}

__all__ = ["__version__", *_API_EXPORTS]


def __getattr__(name: str):
    if name in _API_EXPORTS:
        from . import api

        value = getattr(api, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'hippos' has no attribute {name!r}")
