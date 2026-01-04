from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx


class GroqClient:
    """
    Groq OpenAI-compatible endpoint.
    Env:
      GROQ_API_KEY (required)
      GROQ_BASE_URL (optional) default https://api.groq.com/openai/v1
      GROQ_MODEL (optional) default llama-3.1-70b-versatile
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile").strip()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 250,
    ) -> str:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is missing")

        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        timeout = httpx.Timeout(25.0, connect=25.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=payload, headers=headers)

        if r.status_code >= 400:
            raise RuntimeError(f"Groq error {r.status_code}: {r.text}")

        data = r.json()
        return (data.get("choices", [{}])[0].get("message", {}) or {}).get("content", "") or ""
