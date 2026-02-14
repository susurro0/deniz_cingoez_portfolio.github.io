# src/finops_llm_router/models/llm_result.py
from pydantic import BaseModel
from typing import Dict


class LLMResult(BaseModel):
    content: str
    usage: Dict[str, int]  # input_tokens, output_tokens
    cost_estimated: float
