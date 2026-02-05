from __future__ import annotations

from dataclasses import dataclass

@dataclass
class ExecutedStep:
    adapter_name: str
    method: str
    params: dict
    result: dict | None = None
