from __future__ import annotations

import logging
from typing import Any
import httpx

from app.ai.base import AIProvider, AIProviderResult
from app.ai.exceptions import AIProviderError
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    """Local Ollama AI Provider using the Ollama HTTP API."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url or "http://host.docker.internal:11434").rstrip("/")
        self.model = model or settings.ollama_model or "llama3.2:3b"
        self.timeout = timeout

    def check_availability(self) -> dict[str, Any]:
        """
        Check if Ollama server is reachable and whether the configured model is installed.
        Returns a dict with availability status, provider name, model, and installed models.
        """
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code != 200:
                    return {
                        "available": False,
                        "provider": "ollama",
                        "model": self.model,
                        "base_url": self.base_url,
                        "error": f"Ollama returned HTTP status {res.status_code}",
                        "installed_models": [],
                    }
                data = res.json()
                raw_models = data.get("models", [])
                installed_names = [m.get("name", "") for m in raw_models if m.get("name")]

                model_base = self.model.split(":")[0]
                has_model = any(
                    name == self.model
                    or name.startswith(f"{self.model}:")
                    or name.split(":")[0] == model_base
                    for name in installed_names
                )

                if not has_model:
                    return {
                        "available": False,
                        "provider": "ollama",
                        "model": self.model,
                        "base_url": self.base_url,
                        "error": (
                            f"Model '{self.model}' is not installed in Ollama. "
                            f"Run: 'ollama pull {self.model}'"
                        ),
                        "installed_models": installed_names,
                    }

                return {
                    "available": True,
                    "provider": "ollama",
                    "model": self.model,
                    "base_url": self.base_url,
                    "installed_models": installed_names,
                }
        except (httpx.ConnectError, httpx.NetworkError):
            return {
                "available": False,
                "provider": "ollama",
                "model": self.model,
                "base_url": self.base_url,
                "error": (
                    f"Ollama server is unreachable at {self.base_url}. "
                    "Ensure Ollama is running ('ollama serve') and accessible from Docker."
                ),
                "installed_models": [],
            }
        except httpx.TimeoutException:
            return {
                "available": False,
                "provider": "ollama",
                "model": self.model,
                "base_url": self.base_url,
                "error": f"Timeout connecting to Ollama at {self.base_url}.",
                "installed_models": [],
            }
        except Exception as exc:
            return {
                "available": False,
                "provider": "ollama",
                "model": self.model,
                "base_url": self.base_url,
                "error": f"Unexpected error checking Ollama: {exc}",
                "installed_models": [],
            }

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIProviderResult:
        """
        Generate content using Ollama HTTP API (via /api/chat endpoint).
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        options: dict[str, Any] = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if options:
            payload["options"] = options

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(f"{self.base_url}/api/chat", json=payload)

                if res.status_code == 404:
                    raise AIProviderError(
                        f"Ollama model '{self.model}' was not found. Download it with: 'ollama pull {self.model}'",
                        status_code=404,
                    )
                elif res.status_code != 200:
                    raise AIProviderError(
                        f"Ollama API error ({res.status_code}): {res.text}",
                        status_code=502,
                    )

                data = res.json()
                message = data.get("message", {})
                content = message.get("content", "")

                prompt_tokens = data.get("prompt_eval_count")
                completion_tokens = data.get("eval_count")
                total_tokens = None
                if prompt_tokens is not None or completion_tokens is not None:
                    total_tokens = (prompt_tokens or 0) + (completion_tokens or 0)

                return AIProviderResult(
                    content=content.strip(),
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                )
        except httpx.ConnectError as exc:
            raise AIProviderError(
                f"Ollama server is unreachable at {self.base_url}. Ensure Ollama is running and accessible.",
                status_code=503,
            ) from exc
        except httpx.TimeoutException as exc:
            raise AIProviderError(
                f"Ollama request timed out after {self.timeout}s while generating response.",
                status_code=504,
            ) from exc
        except httpx.RequestError as exc:
            raise AIProviderError(
                f"Ollama connection error: {exc}",
                status_code=502,
            ) from exc
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError(
                f"Unexpected error in Ollama generation: {exc}",
                status_code=502,
            ) from exc
