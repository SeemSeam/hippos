"""YAML configuration loading with Pydantic validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field

from ..constants import (
    DEFAULT_MAX_CONCURRENT,
    DEFAULT_RETRY_MAX,
    DEFAULT_TIMEOUT,
)
from .gateway_models import (
    apply_gateway_route_defaults,
    llm_model_explicit,
    llm_route_explicit,
    resolved_gateway_task_models,
)
from .gateway_support import (
    discover_gateway_config,
    load_gateway_backend_profile,
)
from .merge_support import (
    infer_project_root,
    load_yaml_dict,
    merge_dicts,
    merge_dicts_skipping_empty_defaults,
    normalize_str,
)
from ..integration.llmgateway_runtime import (
    describe_user_gateway_runtime_issue,
    load_user_gateway_runtime_profile,
)
from ..paths import config_file_for_read
from ..user_llm_config import (
    describe_user_llm_config_issue,
    load_user_llm_config,
    resolve_user_llm_config_file,
)


class LLMPhaseModels(BaseModel):
    phase_1: str = "anthropic/claude-haiku-4-5-20251001"
    phase_2a: str = "anthropic/claude-sonnet-4-5-20250929"
    phase_2b: str = "anthropic/claude-haiku-4-5-20251001"
    phase_3a: str = "anthropic/claude-haiku-4-5-20251001"
    phase_3b: str = "anthropic/claude-sonnet-4-5-20250929"
    architect: str = "anthropic/claude-sonnet-4-5-20250929"


class LLMTemperature(BaseModel):
    phase_1: float = 0.0
    phase_2a: float = 0.0
    phase_2b: float = 0.0
    phase_3a: float = 0.2
    phase_3b: float = 0.3
    architect: float = 0.3


class LLMReasoningEffort(BaseModel):
    phase_1: str = ""
    phase_2a: str = ""
    phase_2b: str = ""
    phase_3a: str = ""
    phase_3b: str = ""
    architect: str = ""


class LLMPhaseTiers(BaseModel):
    phase_1: str = "weak"
    phase_2a: str = "strong"
    phase_2b: str = "weak"
    phase_3a: str = "weak"
    phase_3b: str = "strong"
    architect: str = "strong"


class LLMConfig(BaseModel):
    phase_tiers: LLMPhaseTiers = Field(default_factory=LLMPhaseTiers)
    phase_models: LLMPhaseModels = Field(default_factory=LLMPhaseModels)
    phase_reasoning_effort: LLMReasoningEffort = Field(default_factory=LLMReasoningEffort)
    strong_model: str = ""
    weak_model: str = ""
    strong_reasoning_effort: str = ""
    weak_reasoning_effort: str = ""
    max_concurrent: int = DEFAULT_MAX_CONCURRENT
    retry_max: int = DEFAULT_RETRY_MAX
    timeout: int = DEFAULT_TIMEOUT
    temperature: LLMTemperature = Field(default_factory=LLMTemperature)
    fallback_model: str = "anthropic/claude-haiku-4-5-20251001"
    litellm_provider: Optional[str] = None
    provider_type: Optional[str] = None
    api_style: Optional[str] = None
    base_url: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    extra_headers: dict[str, str] = Field(default_factory=dict)
    model_map: dict[str, str] = Field(default_factory=dict)
    auto_from_llm_gateway: bool = True
    gateway_config_path: Optional[str] = None
    use_backend_task_models: bool = True


class HipposConfig(BaseModel):
    target: str = "."
    output_dir: str = ".hippos"
    llm: LLMConfig = Field(default_factory=LLMConfig)
    trim_budget: int = 10000
    structure_prompt_profile: str = "auto"
    structure_prompt_map_tokens: int = 5000
    structure_prompt_deep_tokens: int = 16000
    structure_prompt_max_tokens: int = 10000
    structure_prompt_max_chars: int = 10000  # deprecated, use structure_prompt_max_tokens
    structure_prompt_llm_enhance: bool = False
    structure_prompt_archetype: Optional[str] = None

def _merge_user_llm_config(
    raw: dict[str, Any],
    config_path: Optional[Path],
    project_root: Optional[Path],
) -> dict[str, Any]:
    base_raw = load_user_llm_config(resolve_user_llm_config_file())
    if not base_raw:
        return raw

    merged = merge_dicts(base_raw, raw)
    base_llm = base_raw.get("llm", {}) if isinstance(base_raw.get("llm"), dict) else {}
    raw_llm = raw.get("llm", {}) if isinstance(raw.get("llm"), dict) else {}
    if base_llm and raw_llm:
        merged["llm"] = merge_dicts_skipping_empty_defaults(
            base_llm,
            raw_llm,
            defaults=LLMConfig().model_dump(),
        )
    return merged


def _apply_gateway_model_defaults(cfg: HipposConfig, profile: dict[str, Any]) -> None:
    backend_model = normalize_str(profile.get("model"))
    if backend_model:
        cfg.llm.fallback_model = backend_model
    if not cfg.llm.use_backend_task_models:
        return
    resolved = resolved_gateway_task_models(profile, backend_model=backend_model)
    for attr, value in resolved.items():
        setattr(cfg.llm.phase_models, attr, value)


def _apply_gateway_llm_defaults(cfg: HipposConfig, raw: dict[str, Any], cfg_path: Path) -> None:
    """Auto-bind Hippos LLM settings from llm-proxy backend_llm when not explicit."""
    llm_raw = raw.get("llm") if isinstance(raw.get("llm"), dict) else {}
    assert isinstance(llm_raw, dict)

    if not cfg.llm.auto_from_llm_gateway:
        return

    default_llm = LLMConfig()
    route_explicit = llm_route_explicit(llm_raw)
    model_explicit = llm_model_explicit(
        llm_raw,
        default_fallback_model=default_llm.fallback_model,
        default_phase_models=default_llm.phase_models.model_dump(),
    )

    user_profile = load_user_gateway_runtime_profile()
    if user_profile:
        if not route_explicit:
            apply_gateway_route_defaults(cfg, user_profile)
        if not model_explicit:
            _apply_gateway_model_defaults(cfg, user_profile)

    gw_path = discover_gateway_config(cfg_path.parent, cfg.llm.gateway_config_path)
    if gw_path:
        profile = load_gateway_backend_profile(gw_path)
        if profile:
            if not route_explicit:
                apply_gateway_route_defaults(cfg, profile)
            if not model_explicit:
                _apply_gateway_model_defaults(cfg, profile)


def _load_config_from_raw(
    raw: dict[str, Any],
    *,
    config_path: Path | None,
    project_root: Optional[Path],
) -> HipposConfig:
    cfg = HipposConfig(**raw)
    if config_path is not None:
        _apply_gateway_llm_defaults(cfg, raw, config_path)
    elif project_root is not None:
        _apply_gateway_llm_defaults(cfg, raw, project_root / ".hippos" / "config.yaml")
    return cfg


def load_config(config_path: Optional[Path] = None, *, project_root: Optional[Path] = None) -> HipposConfig:
    """Load config from YAML file, falling back to defaults."""
    resolved_config = config_path
    if resolved_config is not None and not resolved_config.exists() and project_root is not None:
        fallback_config = config_file_for_read(project_root)
        if fallback_config.exists():
            resolved_config = fallback_config
    elif resolved_config is None and project_root is not None:
        fallback_config = config_file_for_read(project_root)
        if fallback_config.exists():
            resolved_config = fallback_config

    if resolved_config and resolved_config.exists():
        raw = load_yaml_dict(resolved_config)
        raw = _merge_user_llm_config(raw, resolved_config, project_root)
        if "structure_prompt_max_tokens" not in raw and "structure_prompt_max_chars" in raw:
            raw["structure_prompt_max_tokens"] = raw["structure_prompt_max_chars"]
        return _load_config_from_raw(raw, config_path=resolved_config, project_root=project_root)
    raw = _merge_user_llm_config({}, resolved_config, project_root)
    if raw:
        return _load_config_from_raw(raw, config_path=None, project_root=project_root)
    return HipposConfig()


def llm_is_configured(cfg: HipposConfig) -> bool:
    llm = cfg.llm
    base_url = normalize_str(llm.base_url or llm.api_base)
    api_key = normalize_str(llm.api_key)
    model = normalize_str(llm.strong_model or llm.weak_model or llm.fallback_model)
    return bool(base_url and api_key and model)


def require_llm_configured(cfg: HipposConfig) -> None:
    if llm_is_configured(cfg):
        return
    issues = [
        issue
        for issue in (
            describe_user_gateway_runtime_issue(),
            describe_user_llm_config_issue(),
        )
        if issue
    ]
    if issues:
        raise RuntimeError(
            "hippos requires LLM configuration. "
            f"Detected configuration issue: {'; '.join(issues)}. "
            "Check ~/.llmgateway/config.yaml and ~/.hippos/config.yaml."
        )
    raise RuntimeError(
        "hippos requires LLM configuration. "
        "Set ~/.llmgateway/config.yaml and ~/.hippos/config.yaml first."
    )


def default_config_yaml() -> str:
    """Generate default config.yaml content."""
    cfg = HipposConfig()
    data = {
        "target": cfg.target,
        "output_dir": cfg.output_dir,
        "llm": {
            "phase_tiers": cfg.llm.phase_tiers.model_dump(),
            "temperature": cfg.llm.temperature.model_dump(),
        },
        "trim_budget": cfg.trim_budget,
        "structure_prompt_profile": cfg.structure_prompt_profile,
        "structure_prompt_map_tokens": cfg.structure_prompt_map_tokens,
        "structure_prompt_deep_tokens": cfg.structure_prompt_deep_tokens,
        "structure_prompt_max_tokens": cfg.structure_prompt_max_tokens,
        "structure_prompt_max_chars": cfg.structure_prompt_max_chars,
        "structure_prompt_llm_enhance": cfg.structure_prompt_llm_enhance,
        "structure_prompt_archetype": cfg.structure_prompt_archetype,
    }
    return yaml.dump(data, default_flow_style=False, allow_unicode=True)


# Migration aliases for callers moving from the pre-rename API.
HippoConfig = HipposConfig
