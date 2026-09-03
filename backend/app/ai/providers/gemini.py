from __future__ import annotations

import httpx

from app.ai.base import AIProvider, AIProviderResult
from app.ai.exceptions import AIProviderError
from app.core.config import get_settings


class GeminiProvider(AIProvider):
    """Google Gemini API Provider using generateContent endpoint."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIProviderResult:
        if not self.api_key:
            raise AIProviderError("Gemini API key is not configured", status_code=500)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

        payload: dict = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
        }

        if system_prompt:
            payload["system_instruction"] = {
                "parts": [{"text": system_prompt}]
            }

        generation_config: dict = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens

        if generation_config:
            payload["generationConfig"] = generation_config

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)

                if response.status_code in (401, 403):
                    raise AIProviderError("Invalid Gemini API key or unauthorized", status_code=response.status_code)
                elif response.status_code == 429:
                    raise AIProviderError("Gemini rate limit or quota exceeded", status_code=429)
                elif response.status_code != 200:
                    raise AIProviderError(
                        f"Gemini API error ({response.status_code}): {response.text}",
                        status_code=502,
                    )

                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates or "content" not in candidates[0]:
                    return AIProviderResult(content="")

                parts = candidates[0]["content"].get("parts", [])
                content = "".join(part.get("text", "") for part in parts)
                usage_metadata = data.get("usageMetadata", {})

                return AIProviderResult(
                    content=content.strip(),
                    prompt_tokens=usage_metadata.get("promptTokenCount"),
                    completion_tokens=usage_metadata.get("candidatesTokenCount"),
                    total_tokens=usage_metadata.get("totalTokenCount"),
                )
        except httpx.TimeoutException as exc:
            raise AIProviderError("Gemini request timed out", status_code=504) from exc
        except httpx.RequestError as exc:
            raise AIProviderError(f"Gemini network error: {exc}", status_code=502) from exc
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError(f"Unexpected Gemini error: {exc}", status_code=502) from exc
