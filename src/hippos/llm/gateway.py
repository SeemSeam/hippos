"""Business-facing wrapper around the external llmgateway package."""

from __future__ import annotations

try:
    from llmgateway import Gateway
except ModuleNotFoundError:  # pragma: no cover - dependency-light envs
    class Gateway:
        def __init__(self, runtime_spec):
            self.runtime_spec = runtime_spec

        async def run_json_task(self, *args, **kwargs):
            raise RuntimeError("llmgateway is required for LLM execution.")

from ..config import HipposConfig
from .adapters import runtime_spec_from_hippos_config


class LLMGateway(Gateway):
    """Stable business-facing gateway built from HipposConfig."""

    def __init__(self, config: HipposConfig):
        self.config = config
        super().__init__(runtime_spec_from_hippos_config(config))


def create_llm_gateway(config: HipposConfig) -> LLMGateway:
    return LLMGateway(config)


__all__ = ["LLMGateway", "create_llm_gateway"]
