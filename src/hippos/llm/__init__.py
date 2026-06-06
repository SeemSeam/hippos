"""Hippos-facing LLM entrypoints."""

from __future__ import annotations

__all__ = [
    "LLMGateway",
    "create_llm_gateway",
    "runtime_spec_from_hippo_config",
    "runtime_spec_from_hippos_config",
]


def __getattr__(name: str):
    if name in {"runtime_spec_from_hippo_config", "runtime_spec_from_hippos_config"}:
        from . import adapters

        value = getattr(adapters, name)
        globals()[name] = value
        return value
    if name in {"LLMGateway", "create_llm_gateway"}:
        from . import gateway

        value = getattr(gateway, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'hippos.llm' has no attribute {name!r}")
