from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    from llmgateway import ProviderSpec, RuntimeSpec, TaskSpec
except ModuleNotFoundError:  # pragma: no cover - exercised in dependency-light envs
    @dataclass
    class ProviderSpec:
        provider_type: str = ""
        api_style: str = ""
        base_url: str = ""
        api_key: str = ""
        headers: dict[str, str] = field(default_factory=dict)
        model_map: dict[str, str] = field(default_factory=dict)

    @dataclass
    class TaskSpec:
        model: str = ""
        tier: str = ""
        temperature: float = 0.0
        reasoning_effort: str = ""

    @dataclass
    class RuntimeSpec:
        provider: ProviderSpec = field(default_factory=ProviderSpec)
        fallback_model: str = ""
        strong_model: str = ""
        weak_model: str = ""
        strong_reasoning_effort: str = ""
        weak_reasoning_effort: str = ""
        max_concurrent: int = 1
        retry_max: int = 0
        timeout: float = 90.0
        tasks: dict[str, TaskSpec] = field(default_factory=dict)
        transport_retries: int = 3

from ..config import HipposConfig


def runtime_spec_from_hippos_config(config: HipposConfig) -> RuntimeSpec:
    llm = config.llm
    temperatures = config.llm.temperature.model_dump()
    phase_tiers = config.llm.phase_tiers.model_dump()
    strong_model = str(getattr(llm, "strong_model", "") or "").strip()
    weak_model = str(getattr(llm, "weak_model", "") or "").strip()

    if phase_tiers and (strong_model or weak_model):
        tasks = {
            task_name: TaskSpec(
                tier=str(tier or "").strip().lower(),
                temperature=float(temperatures.get(task_name, 0.0)),
            )
            for task_name, tier in phase_tiers.items()
        }
    else:
        phase_models = config.llm.phase_models.model_dump()
        phase_reasoning_effort = config.llm.phase_reasoning_effort.model_dump()
        tasks = {
            task_name: TaskSpec(
                model=str(model or "").strip(),
                temperature=float(temperatures.get(task_name, 0.0)),
                reasoning_effort=str(phase_reasoning_effort.get(task_name, "") or "").strip().lower(),
            )
            for task_name, model in phase_models.items()
        }

    return RuntimeSpec(
        provider=ProviderSpec(
            provider_type=str(getattr(llm, "provider_type", "") or "").strip(),
            api_style=str(getattr(llm, "api_style", "") or "").strip(),
            base_url=str(llm.base_url or llm.api_base or "").strip(),
            api_key=str(llm.api_key or "").strip(),
            headers=dict(llm.extra_headers or {}),
            model_map=dict(getattr(llm, "model_map", {}) or {}),
        ),
        fallback_model=str(config.llm.fallback_model or weak_model or strong_model or "").strip(),
        strong_model=strong_model,
        weak_model=weak_model,
        strong_reasoning_effort=str(getattr(llm, "strong_reasoning_effort", "") or "").strip().lower(),
        weak_reasoning_effort=str(getattr(llm, "weak_reasoning_effort", "") or "").strip().lower(),
        max_concurrent=max(1, int(config.llm.max_concurrent)),
        retry_max=max(0, int(config.llm.retry_max)),
        timeout=float(config.llm.timeout),
        tasks=tasks,
    )


# Migration alias for callers moving from the old helper name.
runtime_spec_from_hippo_config = runtime_spec_from_hippos_config


__all__ = ["runtime_spec_from_hippo_config", "runtime_spec_from_hippos_config"]
