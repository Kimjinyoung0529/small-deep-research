from __future__ import annotations

import json
import urllib.request
from typing import Protocol


class LLM(Protocol):
    def chat(self, messages: list[dict], max_tokens: int = 512, temperature: float = 0.2) -> str: ...


class OpenAICompatLLM:
    """Any OpenAI-compatible /v1/chat/completions endpoint (llama.cpp llama-server, vLLM, Ollama, ...)."""

    def __init__(self, base_url: str = "http://127.0.0.1:8081/v1", model: str = "local", api_key: str | None = None, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def chat(self, messages: list[dict], max_tokens: int = 512, temperature: float = 0.2) -> str:
        body = json.dumps({"model": self.model, "messages": messages, "max_tokens": max_tokens,
                           "temperature": temperature, "stream": False}).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(self.base_url + "/chat/completions", data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        return (data["choices"][0]["message"].get("content") or "").strip()
