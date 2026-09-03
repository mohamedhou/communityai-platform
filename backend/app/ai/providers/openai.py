from __future__ import annotations

import httpx

from app.ai.base import AIProvider, AIProviderResult
from app.ai.exceptions import AIProviderError
from app.core.config import get_settings


class OpenAIProvider(AIProvider):
    """OpenAI API Provider using Chat Completions endpoint."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIProviderResult:
        if not self.api_key:
            raise AIProviderError("OpenAI API key is not configured", status_code=500)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )

                if response.status_code == 401:
                    raise AIProviderError("Invalid OpenAI API key", status_code=401)
                elif response.status_code == 429:
                    raise AIProviderError("OpenAI rate limit or quota exceeded", status_code=429)
                elif response.status_code != 200:
                    raise AIProviderError(
                        f"OpenAI API error ({response.status_code}): {response.text}",
                        status_code=502,
                    )

                data = response.json()
                content = data["choices"][0]["message"]["content"] or ""
                usage = data.get("usage", {})

                return AIProviderResult(
                    content=content.strip(),
                    prompt_tokens=usage.get("prompt_tokens"),
                    completion_tokens=usage.get("completion_tokens"),
                    total_tokens=usage.get("total_tokens"),
                )
        except httpx.TimeoutException as exc:
            raise AIProviderError("OpenAI request timed out", status_code=504) from exc
        except httpx.RequestError as exc:
            raise AIProviderError(f"OpenAI network error: {exc}", status_code=502) from exc
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError(f"Unexpected OpenAI error: {exc}", status_code=502) from exc
