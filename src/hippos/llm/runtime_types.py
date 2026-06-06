"""Runtime type imports with dependency-light fallbacks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

try:
    from llmgateway import JSONResult, TaskRequest, Validator
except ModuleNotFoundError:  # pragma: no cover - dependency-light envs
    Validator = Callable[[str], list[str]]

    @dataclass
    class TaskRequest:
        task: str
        messages: list[dict] | list[object]

    @dataclass
    class JSONResult:
        task: str
        text: str = ""
        data: object = None
        errors: list[str] = field(default_factory=list)


__all__ = ["JSONResult", "TaskRequest", "Validator"]
