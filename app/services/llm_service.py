"""Centralized text generation with Gemini → Groq → Ollama fallback."""

import logging
import os
import re
from pathlib import Path
from typing import Callable

try:
    from dotenv import load_dotenv
except (
    ImportError
):  # Keeps module imports safe until project dependencies are installed.

    def load_dotenv() -> bool:
        return False


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class LLMServiceError(RuntimeError):
    """Raised when provider selection fails or the locked provider later fails."""


class LLMService:
    """Keeps provider SDK details out of the reasoning agents."""

    PROVIDER_ORDER = ("Gemini", "Groq", "Ollama")
    GEMINI_MODEL = "gemini-3.7-flash"
    # Verified through the configured Groq account's model list.
    GROQ_MODEL = "openai/gpt-oss-20b"

    def __init__(self, timeout_seconds: float = 30.0):
        # Uvicorn's working directory can vary, so load the project's .env
        # explicitly instead of relying on the current shell directory.
        load_dotenv(PROJECT_ROOT / ".env")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL")
        self.ollama_model = os.getenv("OLLAMA_MODEL")
        self.timeout_seconds = timeout_seconds
        # This state belongs to one service instance. BugController creates
        # one service per /analyze request, so it cannot leak across users.
        self._selected_provider: str | None = None
        logger.info(
            "[LLM] Configuration: Gemini key configured=%s, Groq key configured=%s, "
            "Ollama base URL=%s, Ollama model=%s",
            self._has_usable_key(self.gemini_api_key),
            self._has_usable_key(self.groq_api_key),
            self.ollama_base_url or "not configured",
            self.ollama_model or "not configured",
        )

    def generate(self, prompt: str, agent_name: str | None = None) -> str:
        """Generate using one provider selected for this analysis request."""
        provider_functions: dict[str, Callable[[str], str]] = {
            "Gemini": self._generate_gemini,
            "Groq": self._generate_groq,
            "Ollama": self._generate_ollama,
        }

        if self._selected_provider is not None:
            provider = provider_functions[self._selected_provider]
            logger.warning("[LLM] Using selected provider: %s", self._selected_provider)
            if agent_name:
                logger.warning("[LLM] %s → %s", agent_name, self._selected_provider)
            try:
                response = self._normalise_response(provider(prompt))
                if not response:
                    raise ValueError("Provider returned an empty response")
                return response
            except Exception as error:
                reason = self._safe_error_reason(self._selected_provider, error)
                logger.error(
                    "[LLM] Selected provider %s failed during this request: %s",
                    self._selected_provider,
                    reason,
                )
                raise LLMServiceError(
                    f"Selected LLM provider {self._selected_provider} failed during this analysis."
                ) from error

        logger.warning("[LLM] Selecting provider")
        providers = [(name, provider_functions[name]) for name in self.PROVIDER_ORDER]

        for index, (name, provider) in enumerate(providers):
            # Warning-level flow logs remain visible under Uvicorn's default
            # logging setup, while still excluding all credentials.
            logger.warning("[LLM] Trying %s (%d/3)", name, index + 1)
            try:
                response = self._normalise_response(provider(prompt))
                if not response:
                    raise ValueError("Provider returned an empty response")
                self._selected_provider = name
                logger.warning("[LLM] %s succeeded", name)
                logger.warning("[LLM] Provider selected: %s", name)
                if agent_name:
                    logger.warning("[LLM] %s → %s", agent_name, name)
                return response
            except Exception as error:
                reason = self._safe_error_reason(name, error)
                if index < len(providers) - 1:
                    logger.warning("[LLM] %s failed: %s", name, reason)
                    logger.warning("[LLM] Falling back to %s", providers[index + 1][0])
                else:
                    logger.error(
                        "[LLM] %s failed: %s; no providers remain", name, reason
                    )

        raise LLMServiceError(
            "All configured LLM providers are unavailable. Please check provider configuration and availability."
        )

    def _generate_gemini(self, prompt: str) -> str:
        if not self._has_usable_key(self.gemini_api_key):
            raise ValueError("API key missing or placeholder")

        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=self.gemini_api_key,
            http_options=types.HttpOptions(timeout=int(self.timeout_seconds * 1000)),
        )
        response = client.models.generate_content(
            model=self.GEMINI_MODEL,
            contents=prompt,
        )
        return response.text or ""

    def _generate_groq(self, prompt: str) -> str:
        if not self._has_usable_key(self.groq_api_key):
            raise ValueError("API key missing or placeholder")

        from groq import Groq

        client = Groq(api_key=self.groq_api_key, timeout=self.timeout_seconds)
        completion = client.chat.completions.create(
            model=self.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return completion.choices[0].message.content or ""

    def _generate_ollama(self, prompt: str) -> str:
        if not self.ollama_base_url or not self.ollama_model:
            raise ValueError("base URL or model missing")

        import ollama

        client = ollama.Client(host=self.ollama_base_url, timeout=self.timeout_seconds)
        response = client.chat(
            model=self.ollama_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]

    @staticmethod
    def _normalise_response(response: str) -> str:
        """Accept plain text and text wrapped in Markdown code fences."""
        text = str(response or "").strip()
        text = re.sub(r"^```(?:json|text)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    @staticmethod
    def _has_usable_key(value: str | None) -> bool:
        """Treat empty template values as absent while never logging the key."""
        if not value:
            return False
        lowered = value.strip().lower()
        return bool(lowered) and "your_" not in lowered and "_key_here" not in lowered

    def _safe_error_reason(self, provider: str, error: Exception) -> str:
        """Return diagnostic information without exposing request headers or keys."""
        if isinstance(error, ValueError):
            return str(error)

        status_code = getattr(error, "status_code", None)
        response = getattr(error, "response", None)
        status_code = status_code or getattr(response, "status_code", None)
        if status_code in (401, 403):
            return f"authentication error (HTTP {status_code})"
        if status_code == 404:
            return "model or endpoint unavailable (HTTP 404)"
        if status_code == 429:
            return "rate limit reached (HTTP 429)"
        if status_code:
            return f"provider API error (HTTP {status_code})"

        error_name = type(error).__name__.lower()
        if "timeout" in error_name:
            return "request timed out"
        if "connect" in error_name or "connection" in error_name:
            if provider == "Ollama":
                return f"connection failed at {self.ollama_base_url}"
            return "network connection failed"
        if "import" in error_name or isinstance(error, ImportError):
            return "provider SDK is not installed"
        if "notfound" in error_name:
            return "model unavailable"
        return f"provider request failed ({type(error).__name__})"
