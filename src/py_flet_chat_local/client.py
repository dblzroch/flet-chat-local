"""Ollama API client for flet-chat-local."""

import json
from collections.abc import Iterator
from typing import Any, Self

import httpx


class OllamaClient:
    """Client for the Ollama local LLM API."""

    def __init__(self: Self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=60.0)

    def list_models(self: Self) -> list[str]:
        """Return the list of available model names."""
        resp = self.client.get("/api/tags")
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]

    def chat_stream(
        self: Self, model: str, messages: list[dict[str, Any]], system_prompt: str = ""
    ) -> Iterator[str]:
        """Stream chat responses from Ollama. Yields text chunks."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        with self.client.stream("POST", "/api/chat", json=payload) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "message" in data and "content" in data["message"]:
                    yield data["message"]["content"]
                if data.get("done", False):
                    break

    def close(self: Self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self: Self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
